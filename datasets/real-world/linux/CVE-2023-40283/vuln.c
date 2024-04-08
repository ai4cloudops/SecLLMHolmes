#include <linux/module.h>
#include <linux/export.h>
#include <linux/filter.h>
#include <linux/sched/signal.h>

#include <net/bluetooth/bluetooth.h>
#include <net/bluetooth/hci_core.h>
#include <net/bluetooth/l2cap.h>

#include "smp.h"

static struct bt_sock_list l2cap_sk_list = {
	.lock = __RW_LOCK_UNLOCKED(l2cap_sk_list.lock)
};

static const struct proto_ops l2cap_sock_ops;
static void l2cap_sock_init(struct sock *sk, struct sock *parent);
static struct sock *l2cap_sock_alloc(struct net *net, struct socket *sock,
				     int proto, gfp_t prio, int kern);

bool l2cap_is_socket(struct socket *sock)
{
	return sock && sock->ops == &l2cap_sock_ops;
}
EXPORT_SYMBOL(l2cap_is_socket);

static int l2cap_sock_release(struct socket *sock)
{
	struct sock *sk = sock->sk;
	int err;
	struct l2cap_chan *chan;

	BT_DBG("sock %p, sk %p", sock, sk);

	if (!sk)
		return 0;

	bt_sock_unlink(&l2cap_sk_list, sk);

	err = l2cap_sock_shutdown(sock, SHUT_RDWR);
	chan = l2cap_pi(sk)->chan;

	l2cap_chan_hold(chan);
	l2cap_chan_lock(chan);

	sock_orphan(sk);
	l2cap_sock_kill(sk);

	l2cap_chan_unlock(chan);
	l2cap_chan_put(chan);

	return err;
}

static void l2cap_sock_cleanup_listen(struct sock *parent)
{
	struct sock *sk;

	BT_DBG("parent %p state %s", parent,
	       state_to_string(parent->sk_state));

	/* Close not yet accepted channels */
	while ((sk = bt_accept_dequeue(parent, NULL))) {
		struct l2cap_chan *chan = l2cap_pi(sk)->chan;

		BT_DBG("child chan %p state %s", chan,
		       state_to_string(chan->state));

		l2cap_chan_hold(chan);
		l2cap_chan_lock(chan);

		__clear_chan_timer(chan);
		l2cap_chan_close(chan, ECONNRESET);
		l2cap_sock_kill(sk);

		l2cap_chan_unlock(chan);
		l2cap_chan_put(chan);
	}
}

static void l2cap_sock_teardown_cb(struct l2cap_chan *chan, int err)
{
	struct sock *sk = chan->data;
	struct sock *parent;

	if (!sk)
		return;

	BT_DBG("chan %p state %s", chan, state_to_string(chan->state));

	/* This callback can be called both for server (BT_LISTEN)
	 * sockets as well as "normal" ones. To avoid lockdep warnings
	 * with child socket locking (through l2cap_sock_cleanup_listen)
	 * we need separation into separate nesting levels. The simplest
	 * way to accomplish this is to inherit the nesting level used
	 * for the channel.
	 */
	lock_sock_nested(sk, atomic_read(&chan->nesting));

	parent = bt_sk(sk)->parent;

	switch (chan->state) {
	case BT_OPEN:
	case BT_BOUND:
	case BT_CLOSED:
		break;
	case BT_LISTEN:
		l2cap_sock_cleanup_listen(sk);
		sk->sk_state = BT_CLOSED;
		chan->state = BT_CLOSED;

		break;
	default:
		sk->sk_state = BT_CLOSED;
		chan->state = BT_CLOSED;

		sk->sk_err = err;

		if (parent) {
			bt_accept_unlink(sk);
			parent->sk_data_ready(parent);
		} else {
			sk->sk_state_change(sk);
		}

		break;
	}
	release_sock(sk);

	/* Only zap after cleanup to avoid use after free race */
	sock_set_flag(sk, SOCK_ZAPPED);

}

static void l2cap_sock_state_change_cb(struct l2cap_chan *chan, int state,
				       int err)
{
	struct sock *sk = chan->data;

	sk->sk_state = state;

	if (err)
		sk->sk_err = err;
}

static struct sk_buff *l2cap_sock_alloc_skb_cb(struct l2cap_chan *chan,
					       unsigned long hdr_len,
					       unsigned long len, int nb)
{
	struct sock *sk = chan->data;
	struct sk_buff *skb;
	int err;

	l2cap_chan_unlock(chan);
	skb = bt_skb_send_alloc(sk, hdr_len + len, nb, &err);
	l2cap_chan_lock(chan);

	if (!skb)
		return ERR_PTR(err);

	/* Channel lock is released before requesting new skb and then
	 * reacquired thus we need to recheck channel state.
	 */
	if (chan->state != BT_CONNECTED) {
		kfree_skb(skb);
		return ERR_PTR(-ENOTCONN);
	}

	skb->priority = sk->sk_priority;

	bt_cb(skb)->l2cap.chan = chan;

	return skb;
}

static void l2cap_sock_ready_cb(struct l2cap_chan *chan)
{
	struct sock *sk = chan->data;
	struct sock *parent;

	lock_sock(sk);

	parent = bt_sk(sk)->parent;

	BT_DBG("sk %p, parent %p", sk, parent);

	sk->sk_state = BT_CONNECTED;
	sk->sk_state_change(sk);

	if (parent)
		parent->sk_data_ready(parent);

	release_sock(sk);
}

static void l2cap_sock_defer_cb(struct l2cap_chan *chan)
{
	struct sock *parent, *sk = chan->data;

	lock_sock(sk);

	parent = bt_sk(sk)->parent;
	if (parent)
		parent->sk_data_ready(parent);

	release_sock(sk);
}

static void l2cap_sock_resume_cb(struct l2cap_chan *chan)
{
	struct sock *sk = chan->data;

	if (test_and_clear_bit(FLAG_PENDING_SECURITY, &chan->flags)) {
		sk->sk_state = BT_CONNECTED;
		chan->state = BT_CONNECTED;
	}

	clear_bit(BT_SK_SUSPEND, &bt_sk(sk)->flags);
	sk->sk_state_change(sk);
}

static void l2cap_sock_set_shutdown_cb(struct l2cap_chan *chan)
{
	struct sock *sk = chan->data;

	lock_sock(sk);
	sk->sk_shutdown = SHUTDOWN_MASK;
	release_sock(sk);
}

static long l2cap_sock_get_sndtimeo_cb(struct l2cap_chan *chan)
{
	struct sock *sk = chan->data;

	return sk->sk_sndtimeo;
}

static struct pid *l2cap_sock_get_peer_pid_cb(struct l2cap_chan *chan)
{
	struct sock *sk = chan->data;

	return sk->sk_peer_pid;
}

static void l2cap_sock_suspend_cb(struct l2cap_chan *chan)
{
	struct sock *sk = chan->data;

	set_bit(BT_SK_SUSPEND, &bt_sk(sk)->flags);
	sk->sk_state_change(sk);
}

static int l2cap_sock_filter(struct l2cap_chan *chan, struct sk_buff *skb)
{
	struct sock *sk = chan->data;

	switch (chan->mode) {
	case L2CAP_MODE_ERTM:
	case L2CAP_MODE_STREAMING:
		return sk_filter(sk, skb);
	}

	return 0;
}

static const struct l2cap_ops l2cap_chan_ops = {
	.name			= "L2CAP Socket Interface",
	.new_connection		= l2cap_sock_new_connection_cb,
	.recv			= l2cap_sock_recv_cb,
	.close			= l2cap_sock_close_cb,
	.teardown		= l2cap_sock_teardown_cb,
	.state_change		= l2cap_sock_state_change_cb,
	.ready			= l2cap_sock_ready_cb,
	.defer			= l2cap_sock_defer_cb,
	.resume			= l2cap_sock_resume_cb,
	.suspend		= l2cap_sock_suspend_cb,
	.set_shutdown		= l2cap_sock_set_shutdown_cb,
	.get_sndtimeo		= l2cap_sock_get_sndtimeo_cb,
	.get_peer_pid		= l2cap_sock_get_peer_pid_cb,
	.alloc_skb		= l2cap_sock_alloc_skb_cb,
	.filter			= l2cap_sock_filter,
};

static void l2cap_sock_destruct(struct sock *sk)
{
	BT_DBG("sk %p", sk);

	if (l2cap_pi(sk)->chan) {
		l2cap_pi(sk)->chan->data = NULL;
		l2cap_chan_put(l2cap_pi(sk)->chan);
	}

	if (l2cap_pi(sk)->rx_busy_skb) {
		kfree_skb(l2cap_pi(sk)->rx_busy_skb);
		l2cap_pi(sk)->rx_busy_skb = NULL;
	}

	skb_queue_purge(&sk->sk_receive_queue);
	skb_queue_purge(&sk->sk_write_queue);
}

static void l2cap_skb_msg_name(struct sk_buff *skb, void *msg_name,
			       int *msg_namelen)
{
	DECLARE_SOCKADDR(struct sockaddr_l2 *, la, msg_name);

	memset(la, 0, sizeof(struct sockaddr_l2));
	la->l2_family = AF_BLUETOOTH;
	la->l2_psm = bt_cb(skb)->l2cap.psm;
	bacpy(&la->l2_bdaddr, &bt_cb(skb)->l2cap.bdaddr);

	*msg_namelen = sizeof(struct sockaddr_l2);
}

static void l2cap_sock_init(struct sock *sk, struct sock *parent)
{
	struct l2cap_chan *chan = l2cap_pi(sk)->chan;

	BT_DBG("sk %p", sk);

	if (parent) {
		struct l2cap_chan *pchan = l2cap_pi(parent)->chan;

		sk->sk_type = parent->sk_type;
		bt_sk(sk)->flags = bt_sk(parent)->flags;

		chan->chan_type = pchan->chan_type;
		chan->imtu = pchan->imtu;
		chan->omtu = pchan->omtu;
		chan->conf_state = pchan->conf_state;
		chan->mode = pchan->mode;
		chan->fcs  = pchan->fcs;
		chan->max_tx = pchan->max_tx;
		chan->tx_win = pchan->tx_win;
		chan->tx_win_max = pchan->tx_win_max;
		chan->sec_level = pchan->sec_level;
		chan->flags = pchan->flags;
		chan->tx_credits = pchan->tx_credits;
		chan->rx_credits = pchan->rx_credits;

		if (chan->chan_type == L2CAP_CHAN_FIXED) {
			chan->scid = pchan->scid;
			chan->dcid = pchan->scid;
		}

		security_sk_clone(parent, sk);
	} else {
		switch (sk->sk_type) {
		case SOCK_RAW:
			chan->chan_type = L2CAP_CHAN_RAW;
			break;
		case SOCK_DGRAM:
			chan->chan_type = L2CAP_CHAN_CONN_LESS;
			bt_sk(sk)->skb_msg_name = l2cap_skb_msg_name;
			break;
		case SOCK_SEQPACKET:
		case SOCK_STREAM:
			chan->chan_type = L2CAP_CHAN_CONN_ORIENTED;
			break;
		}

		chan->imtu = L2CAP_DEFAULT_MTU;
		chan->omtu = 0;
		if (!disable_ertm && sk->sk_type == SOCK_STREAM) {
			chan->mode = L2CAP_MODE_ERTM;
			set_bit(CONF_STATE2_DEVICE, &chan->conf_state);
		} else {
			chan->mode = L2CAP_MODE_BASIC;
		}

		l2cap_chan_set_defaults(chan);
	}

	/* Default config options */
	chan->flush_to = L2CAP_DEFAULT_FLUSH_TO;

	chan->data = sk;
	chan->ops = &l2cap_chan_ops;
}

static struct proto l2cap_proto = {
	.name		= "L2CAP",
	.owner		= THIS_MODULE,
	.obj_size	= sizeof(struct l2cap_pinfo)
};

static struct sock *l2cap_sock_alloc(struct net *net, struct socket *sock,
				     int proto, gfp_t prio, int kern)
{
	struct sock *sk;
	struct l2cap_chan *chan;

	sk = sk_alloc(net, PF_BLUETOOTH, prio, &l2cap_proto, kern);
	if (!sk)
		return NULL;

	sock_init_data(sock, sk);
	INIT_LIST_HEAD(&bt_sk(sk)->accept_q);

	sk->sk_destruct = l2cap_sock_destruct;
	sk->sk_sndtimeo = L2CAP_CONN_TIMEOUT;

	sock_reset_flag(sk, SOCK_ZAPPED);

	sk->sk_protocol = proto;
	sk->sk_state = BT_OPEN;

	chan = l2cap_chan_create();
	if (!chan) {
		sk_free(sk);
		return NULL;
	}

	l2cap_chan_hold(chan);

	l2cap_pi(sk)->chan = chan;

	return sk;
}

static int l2cap_sock_create(struct net *net, struct socket *sock, int protocol,
			     int kern)
{
	struct sock *sk;

	BT_DBG("sock %p", sock);

	sock->state = SS_UNCONNECTED;

	if (sock->type != SOCK_SEQPACKET && sock->type != SOCK_STREAM &&
	    sock->type != SOCK_DGRAM && sock->type != SOCK_RAW)
		return -ESOCKTNOSUPPORT;

	if (sock->type == SOCK_RAW && !kern && !capable(CAP_NET_RAW))
		return -EPERM;

	sock->ops = &l2cap_sock_ops;

	sk = l2cap_sock_alloc(net, sock, protocol, GFP_ATOMIC, kern);
	if (!sk)
		return -ENOMEM;

	l2cap_sock_init(sk, NULL);
	bt_sock_link(&l2cap_sk_list, sk);
	return 0;
}

static const struct proto_ops l2cap_sock_ops = {
	.family		= PF_BLUETOOTH,
	.owner		= THIS_MODULE,
	.release	= l2cap_sock_release,
	.bind		= l2cap_sock_bind,
	.connect	= l2cap_sock_connect,
	.listen		= l2cap_sock_listen,
	.accept		= l2cap_sock_accept,
	.getname	= l2cap_sock_getname,
	.sendmsg	= l2cap_sock_sendmsg,
	.recvmsg	= l2cap_sock_recvmsg,
	.poll		= bt_sock_poll,
	.ioctl		= bt_sock_ioctl,
	.gettstamp	= sock_gettstamp,
	.mmap		= sock_no_mmap,
	.socketpair	= sock_no_socketpair,
	.shutdown	= l2cap_sock_shutdown,
	.setsockopt	= l2cap_sock_setsockopt,
	.getsockopt	= l2cap_sock_getsockopt
};

static const struct net_proto_family l2cap_sock_family_ops = {
	.family	= PF_BLUETOOTH,
	.owner	= THIS_MODULE,
	.create	= l2cap_sock_create,
};

int __init l2cap_init_sockets(void)
{
	int err;

	BUILD_BUG_ON(sizeof(struct sockaddr_l2) > sizeof(struct sockaddr));

	err = proto_register(&l2cap_proto, 0);
	if (err < 0)
		return err;

	err = bt_sock_register(BTPROTO_L2CAP, &l2cap_sock_family_ops);
	if (err < 0) {
		BT_ERR("L2CAP socket registration failed");
		goto error;
	}

	err = bt_procfs_init(&init_net, "l2cap", &l2cap_sk_list,
			     NULL);
	if (err < 0) {
		BT_ERR("Failed to create L2CAP proc file");
		bt_sock_unregister(BTPROTO_L2CAP);
		goto error;
	}

	BT_INFO("L2CAP socket layer initialized");

	return 0;

error:
	proto_unregister(&l2cap_proto);
	return err;
}

void l2cap_cleanup_sockets(void)
{
	bt_procfs_cleanup(&init_net, "l2cap");
	bt_sock_unregister(BTPROTO_L2CAP);
	proto_unregister(&l2cap_proto);
}