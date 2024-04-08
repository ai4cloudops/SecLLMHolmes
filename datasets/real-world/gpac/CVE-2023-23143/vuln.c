#include <gpac/internal/media_dev.h>
#include <gpac/constants.h>
#include <gpac/mpeg4_odf.h>
#include <gpac/maths.h>
#include <gpac/avparse.h>

#ifndef GPAC_DISABLE_OGG
#include <gpac/internal/ogg.h>
#endif

typedef struct
{
	AVC_SPS sps[32]; /* range allowed in the spec is 0..31 */
	s8 sps_active_idx, pps_active_idx;	/*currently active sps; must be initalized to -1 in order to discard not yet decodable SEIs*/

	AVC_PPS pps[255];

	AVCSliceInfo s_info;
	AVCSei sei;

	Bool is_svc;
	u8 last_nal_type_parsed;
	s8 last_ps_idx, last_sps_idx;
} AVCState;

static s32 avc_parse_slice(GF_BitStream *bs, AVCState *avc, Bool svc_idr_flag, AVCSliceInfo *si)
{
	s32 pps_id, num_ref_idx_l0_active_minus1 = 0, num_ref_idx_l1_active_minus1 = 0;
	/*s->current_picture.reference= h->nal_ref_idc != 0;*/
	gf_bs_read_ue_log(bs, "first_mb_in_slice");
	si->slice_type = gf_bs_read_ue_log(bs, "slice_type");
	if (si->slice_type > 9) return -1;

	pps_id = gf_bs_read_ue_log(bs, "pps_id");
	if ((pps_id<0) || (pps_id > 255)) return -1;
	si->pps = &avc->pps[pps_id];
	if (!si->pps->slice_group_count) return -2;
	if (si->pps->sps_id>=255) return -1;
	si->sps = &avc->sps[si->pps->sps_id];
	if (!si->sps->log2_max_frame_num) return -2;
	avc->sps_active_idx = si->pps->sps_id;
	avc->pps_active_idx = pps_id;
	si->frame_num = gf_bs_read_int_log(bs, si->sps->log2_max_frame_num, "frame_num");
	si->field_pic_flag = 0;
	si->bottom_field_flag = 0;
	if (!si->sps->frame_mbs_only_flag) {
		si->field_pic_flag = gf_bs_read_int_log(bs, 1, "field_pic_flag");
		if (si->field_pic_flag)
			si->bottom_field_flag = gf_bs_read_int_log(bs, 1, "bottom_field_flag");
	}
	if ((si->nal_unit_type == GF_AVC_NALU_IDR_SLICE) || svc_idr_flag)
		si->idr_pic_id = gf_bs_read_ue_log(bs, "idr_pic_id");
	if (si->sps->poc_type == 0) {
		si->poc_lsb = gf_bs_read_int_log(bs, si->sps->log2_max_poc_lsb, "poc_lsb");
		if (si->pps->pic_order_present && !si->field_pic_flag) {
			si->delta_poc_bottom = gf_bs_read_se_log(bs, "poc_lsb");
		}
	}
	else if ((si->sps->poc_type == 1) && !si->sps->delta_pic_order_always_zero_flag) {
		si->delta_poc[0] = gf_bs_read_se_log(bs, "delta_poc0");
		if ((si->pps->pic_order_present == 1) && !si->field_pic_flag)
			si->delta_poc[1] = gf_bs_read_se_log(bs, "delta_poc1");
	}
	if (si->pps->redundant_pic_cnt_present) {
		si->redundant_pic_cnt = gf_bs_read_ue_log(bs, "redundant_pic_cnt");
	}
	if (si->slice_type % 5 == GF_AVC_TYPE_B) {
		gf_bs_read_int_log(bs, 1, "direct_spatial_mv_pred_flag");
	}
	num_ref_idx_l0_active_minus1 = si->pps->num_ref_idx_l0_default_active_minus1;
	num_ref_idx_l1_active_minus1 = si->pps->num_ref_idx_l1_default_active_minus1;
	if (si->slice_type % 5 == GF_AVC_TYPE_P || si->slice_type % 5 == GF_AVC_TYPE_SP || si->slice_type % 5 == GF_AVC_TYPE_B) {
		Bool num_ref_idx_active_override_flag = gf_bs_read_int_log(bs, 1, "num_ref_idx_active_override_flag");
		if (num_ref_idx_active_override_flag) {
			num_ref_idx_l0_active_minus1 = gf_bs_read_ue_log(bs, "num_ref_idx_l0_active_minus1");
			if (si->slice_type % 5 == GF_AVC_TYPE_B) {
				num_ref_idx_l1_active_minus1 = gf_bs_read_ue_log(bs, "num_ref_idx_l1_active_minus1");
			}
		}
	}
	if (si->nal_unit_type == 20 || si->nal_unit_type == 21) {
		//ref_pic_list_mvc_modification(); /* specified in Annex H */
		GF_LOG(GF_LOG_ERROR, GF_LOG_CODING, ("[avc-h264] unimplemented ref_pic_list_mvc_modification() in slide header\n"));
		assert(0);
		return -1;
	}
	else {
		ref_pic_list_modification(bs, si->slice_type);
	}
	if ((si->pps->weighted_pred_flag && (si->slice_type % 5 == GF_AVC_TYPE_P || si->slice_type % 5 == GF_AVC_TYPE_SP))
		|| (si->pps->weighted_bipred_idc == 1 && si->slice_type % 5 == GF_AVC_TYPE_B)) {
		avc_pred_weight_table(bs, si->slice_type, si->sps->ChromaArrayType, num_ref_idx_l0_active_minus1, num_ref_idx_l1_active_minus1);
	}
	if (si->nal_ref_idc != 0) {
		dec_ref_pic_marking(bs, (si->nal_unit_type == GF_AVC_NALU_IDR_SLICE));
	}
	if (si->pps->entropy_coding_mode_flag && si->slice_type % 5 != GF_AVC_TYPE_I && si->slice_type % 5 != GF_AVC_TYPE_SI) {
		gf_bs_read_ue_log(bs, "cabac_init_idc");
	}
	/*slice_qp_delta = */gf_bs_read_se(bs);
	if (si->slice_type % 5 == GF_AVC_TYPE_SP || si->slice_type % 5 == GF_AVC_TYPE_SI) {
		if (si->slice_type % 5 == GF_AVC_TYPE_SP) {
			gf_bs_read_int_log(bs, 1, "sp_for_switch_flag");
		}
		gf_bs_read_se_log(bs, "slice_qs_delta");
	}
	if (si->pps->deblocking_filter_control_present_flag) {
		if (gf_bs_read_ue_log(bs, "disable_deblocking_filter_idc") != 1) {
			gf_bs_read_se_log(bs, "slice_alpha_c0_offset_div2");
			gf_bs_read_se_log(bs, "slice_beta_offset_div2");
		}
	}
	if (si->pps->slice_group_count > 1 && si->pps->mb_slice_group_map_type >= 3 && si->pps->mb_slice_group_map_type <= 5) {
		gf_bs_read_int_log(bs, (u32)ceil(log1p((si->pps->pic_size_in_map_units_minus1 + 1) / (si->pps->slice_group_change_rate_minus1 + 1) ) / log(2)), "slice_group_change_cycle");
	}
	return 0;
}