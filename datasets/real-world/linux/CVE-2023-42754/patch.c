#define pr_fmt(fmt) "IPv4: " fmt

#include <linux/module.h>
#include <linux/bitops.h>
#include <linux/kernel.h>
#include <linux/mm.h>
#include <linux/memblock.h>
#include <linux/socket.h>
#include <linux/errno.h>
#include <linux/in.h>
#include <linux/inet.h>
#include <linux/netdevice.h>
#include <linux/proc_fs.h>
#include <linux/init.h>
#include <linux/skbuff.h>
#include <linux/inetdevice.h>
#include <linux/igmp.h>
#include <linux/pkt_sched.h>
#include <linux/mroute.h>
#include <linux/netfilter_ipv4.h>
#include <linux/random.h>
#include <linux/rcupdate.h>
#include <linux/slab.h>
#include <linux/jhash.h>
#include <net/dst.h>
#include <net/dst_metadata.h>
#include <net/inet_dscp.h>
#include <net/net_namespace.h>
#include <net/ip.h>
#include <net/route.h>
#include <net/inetpeer.h>
#include <net/sock.h>
#include <net/ip_fib.h>
#include <net/nexthop.h>
#include <net/tcp.h>
#include <net/icmp.h>
#include <net/xfrm.h>
#include <net/lwtunnel.h>
#include <net/netevent.h>
#include <net/rtnetlink.h>
#ifdef CONFIG_SYSCTL
#include <linux/sysctl.h>
#endif
#include <net/secure_seq.h>
#include <net/ip_tunnels.h>

#include "fib_lookup.h"

#define RT_FL_TOS(oldflp4) \
	((oldflp4)->flowi4_tos & (IPTOS_RT_MASK | RTO_ONLINK))

#define RT_GC_TIMEOUT (300*HZ)

#define DEFAULT_MIN_PMTU (512 + 20 + 20)
#define DEFAULT_MTU_EXPIRES (10 * 60 * HZ)
#define DEFAULT_MIN_ADVMSS 256
static int ip_rt_max_size;
static int ip_rt_redirect_number __read_mostly	= 9;
static int ip_rt_redirect_load __read_mostly	= HZ / 50;
static int ip_rt_redirect_silence __read_mostly	= ((HZ / 50) << (9 + 1));
static int ip_rt_error_cost __read_mostly	= HZ;
static int ip_rt_error_burst __read_mostly	= 5 * HZ;

static int ip_rt_gc_timeout __read_mostly	= RT_GC_TIMEOUT;

/*
 *	Interface to generic destination cache.
 */

INDIRECT_CALLABLE_SCOPE
struct dst_entry	*ipv4_dst_check(struct dst_entry *dst, u32 cookie);
static unsigned int	 ipv4_default_advmss(const struct dst_entry *dst);
INDIRECT_CALLABLE_SCOPE
unsigned int		ipv4_mtu(const struct dst_entry *dst);
static struct dst_entry *ipv4_negative_advice(struct dst_entry *dst);
static void		 ipv4_link_failure(struct sk_buff *skb);
static void		 ip_rt_update_pmtu(struct dst_entry *dst, struct sock *sk,
					   struct sk_buff *skb, u32 mtu,
					   bool confirm_neigh);
static void		 ip_do_redirect(struct dst_entry *dst, struct sock *sk,
					struct sk_buff *skb);
static void		ipv4_dst_destroy(struct dst_entry *dst);

static u32 *ipv4_cow_metrics(struct dst_entry *dst, unsigned long old)
{
	WARN_ON(1);
	return NULL;
}

static struct neighbour *ipv4_neigh_lookup(const struct dst_entry *dst,
					   struct sk_buff *skb,
					   const void *daddr);
static void ipv4_confirm_neigh(const struct dst_entry *dst, const void *daddr);

static struct dst_ops ipv4_dst_ops = {
	.family =		AF_INET,
	.check =		ipv4_dst_check,
	.default_advmss =	ipv4_default_advmss,
	.mtu =			ipv4_mtu,
	.cow_metrics =		ipv4_cow_metrics,
	.destroy =		ipv4_dst_destroy,
	.negative_advice =	ipv4_negative_advice,
	.link_failure =		ipv4_link_failure,
	.update_pmtu =		ip_rt_update_pmtu,
	.redirect =		ip_do_redirect,
	.local_out =		__ip_local_out,
	.neigh_lookup =		ipv4_neigh_lookup,
	.confirm_neigh =	ipv4_confirm_neigh,
};

#define ECN_OR_COST(class)	TC_PRIO_##class

const __u8 ip_tos2prio[16] = {
	TC_PRIO_BESTEFFORT,
	ECN_OR_COST(BESTEFFORT),
	TC_PRIO_BESTEFFORT,
	ECN_OR_COST(BESTEFFORT),
	TC_PRIO_BULK,
	ECN_OR_COST(BULK),
	TC_PRIO_BULK,
	ECN_OR_COST(BULK),
	TC_PRIO_INTERACTIVE,
	ECN_OR_COST(INTERACTIVE),
	TC_PRIO_INTERACTIVE,
	ECN_OR_COST(INTERACTIVE),
	TC_PRIO_INTERACTIVE_BULK,
	ECN_OR_COST(INTERACTIVE_BULK),
	TC_PRIO_INTERACTIVE_BULK,
	ECN_OR_COST(INTERACTIVE_BULK)
};
EXPORT_SYMBOL(ip_tos2prio);

static DEFINE_PER_CPU(struct rt_cache_stat, rt_cache_stat);
#define RT_CACHE_STAT_INC(field) raw_cpu_inc(rt_cache_stat.field)

#ifdef CONFIG_PROC_FS

static void ipv4_send_dest_unreach(struct sk_buff *skb)
{
	struct net_device *dev;
	struct ip_options opt;
	int res;

	/* Recompile ip options since IPCB may not be valid anymore.
	 * Also check we have a reasonable ipv4 header.
	 */
	if (!pskb_network_may_pull(skb, sizeof(struct iphdr)) ||
	    ip_hdr(skb)->version != 4 || ip_hdr(skb)->ihl < 5)
		return;

	memset(&opt, 0, sizeof(opt));
	if (ip_hdr(skb)->ihl > 5) {
		if (!pskb_network_may_pull(skb, ip_hdr(skb)->ihl * 4))
			return;
		opt.optlen = ip_hdr(skb)->ihl * 4 - sizeof(struct iphdr);

		rcu_read_lock();
		dev = skb->dev ? skb->dev : skb_rtable(skb)->dst.dev;
		res = __ip_options_compile(dev_net(dev), &opt, skb, NULL);
		rcu_read_unlock();

		if (res)
			return;
	}
	__icmp_send(skb, ICMP_DEST_UNREACH, ICMP_HOST_UNREACH, 0, &opt);
}

static void ipv4_link_failure(struct sk_buff *skb)
{
	struct rtable *rt;

	ipv4_send_dest_unreach(skb);

	rt = skb_rtable(skb);
	if (rt)
		dst_set_expires(&rt->dst, 0);
}