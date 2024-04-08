#include <gpac/filters.h>
#include <gpac/constants.h>
#include <gpac/utf.h>
#include <gpac/xml.h>
#include <gpac/token.h>
#include <gpac/color.h>
#include <gpac/network.h>
#include <gpac/internal/media_dev.h>
#include <gpac/internal/isomedia_dev.h>

#ifndef GPAC_DISABLE_SWF_IMPORT
/* SWF Importer */
#include <gpac/internal/swf_dev.h>
#endif

#if !defined(GPAC_DISABLE_ISOM_WRITE)

#define TTML_NAMESPACE "http://www.w3.org/ns/ttml"

#define CHECK_STR(__str)	\
	if (!__str) { \
		e = gf_import_message(import, GF_BAD_PARAM, "Invalid XML formatting (line %d)", parser.line);	\
		goto exit;	\
	}


typedef struct __txtin_ctx GF_TXTIn;

enum
{
	STXT_MODE_STXT=0,
	STXT_MODE_TX3G,
	STXT_MODE_VTT,
};

struct __txtin_ctx
{
	//opts
	u32 width, height, txtx, txty, fontsize, stxtmod;
	s32 zorder;
	const char *fontname, *lang, *ttml_zero;
	Bool nodefbox, noflush, webvtt, ttml_embed, no_empty;
	u32 timescale;
	GF_Fraction fps;
	Bool ttml_split;
	GF_Fraction64 ttml_cts;
	GF_Fraction ttml_dur, stxtdur;


	GF_FilterPid *ipid, *opid;
	char *file_name;
	u32 fmt;
	u32 playstate;
	//0: not seeking, 1: seek request pending, 2: seek configured, discarding packets up until start_range
	u32 seek_state;
	Double start_range;

	Bool is_loaded;
	Bool is_setup;

	GF_Err (*text_process)(GF_Filter *filter, GF_TXTIn *ctx, GF_FilterPacket *ipck);

	s32 unicode_type;

	FILE *src;

	GF_BitStream *bs_w;
	Bool first_samp;
	Bool hdr_parsed;
	Bool unframed, simple_text;

	//state vars for srt
	u32 state, default_color;
	GF_TextSample *samp;
	u64 start, end, prev_end;
	u32 curLine;
	GF_StyleRecord style;

#ifndef GPAC_DISABLE_VTT
	//WebVTT state
	GF_WebVTTParser *vttparser;
#endif

	//TTXT state
	GF_DOMParser *parser;
	u32 cur_child_idx, nb_children, last_desc_idx;
	GF_List *text_descs;
	Bool last_sample_empty;
	u64 last_sample_duration;
	//TTML state is the same as ttxt plus the timescale and start (webvtt) for cts compute
	u32 txml_timescale;
	u32 current_tt_interval;

	//TTML state
	GF_XMLNode *root_working_copy, *body_node;
	GF_DOMParser *parser_working_copy;
	Bool non_compliant_ttml;
	u32 tick_rate, ttml_fps_num, ttml_fps_den, ttml_sfps;
	GF_List *ttml_resources;
	GF_List *div_nodes_list;
	Bool has_images;

#ifndef GPAC_DISABLE_SWF_IMPORT
	//SWF text
	SWFReader *swf_parse;
	Bool do_suspend;
#endif

	Bool vtt_to_tx3g;
	Bool srt_to_tx3g;

	GF_List *intervals;
	u64 cts_first_interval;
};

typedef struct
{
	u32 size;
	u8 *data;
	Bool global;
} TTMLRes;

typedef struct
{
	s64 begin, end;
	GF_List *resources;
} TTMLInterval;


enum
{
	GF_TXTIN_MODE_NONE = 0,
	GF_TXTIN_MODE_SRT,
	GF_TXTIN_MODE_SUB,
	GF_TXTIN_MODE_TTXT,
	GF_TXTIN_MODE_TEXML,
	GF_TXTIN_MODE_WEBVTT,
	GF_TXTIN_MODE_TTML,
	GF_TXTIN_MODE_SWF_SVG,
	GF_TXTIN_MODE_SSA,
	GF_TXTIN_MODE_SIMPLE,
};

#define REM_TRAIL_MARKS(__str, __sep) while (1) {	\
		u32 _len = (u32) strlen(__str);		\
		if (!_len) break;	\
		_len--;				\
		if (strchr(__sep, __str[_len])) __str[_len] = 0;	\
		else break;	\
	}	\

char *gf_text_get_utf8_line(char *szLine, u32 lineSize, FILE *txt_in, s32 unicode_type)
{
	u32 i, j, len;
	char *sOK;
	char szLineConv[2048];
	unsigned short *sptr;

	memset(szLine, 0, sizeof(char)*lineSize);
	sOK = gf_fgets(szLine, lineSize, txt_in);
	if (!sOK) return NULL;
	if (unicode_type<=1) {
		j=0;
		len = (u32) strlen(szLine);
		for (i=0; i<len; i++) {
			if (!unicode_type && (szLine[i] & 0x80)) {
				/*non UTF8 (likely some win-CP)*/
				if ((szLine[i+1] & 0xc0) != 0x80) {
					szLineConv[j] = 0xc0 | ( (szLine[i] >> 6) & 0x3 );
					j++;
					szLine[i] &= 0xbf;
				}
				/*UTF8 2 bytes char*/
				else if ( (szLine[i] & 0xe0) == 0xc0) {
					szLineConv[j] = szLine[i];
					i++;
					j++;
				}
				/*UTF8 3 bytes char*/
				else if ( (szLine[i] & 0xf0) == 0xe0) {
					szLineConv[j] = szLine[i];
					i++;
					j++;
					szLineConv[j] = szLine[i];
					i++;
					j++;
				}
				/*UTF8 4 bytes char*/
				else if ( (szLine[i] & 0xf8) == 0xf0) {
					szLineConv[j] = szLine[i];
					i++;
					j++;
					szLineConv[j] = szLine[i];
					i++;
					j++;
					szLineConv[j] = szLine[i];
					i++;
					j++;
				} else {
					i+=1;
					continue;
				}
			}
			szLineConv[j] = szLine[i];
			j++;

			if (j >= GF_ARRAY_LENGTH(szLineConv) - 1) {
				GF_LOG(GF_LOG_DEBUG, GF_LOG_PARSER, ("[TXTIn] Line too long to convert to utf8 (len: %d)\n", len));
				break;
			}

		}
		szLineConv[j] = 0;
		strcpy(szLine, szLineConv);
		return sOK;
	}

#ifdef GPAC_BIG_ENDIAN
	if (unicode_type==3)
#else
	if (unicode_type==2)
#endif
	{
		i=0;
		while (1) {
			char c;
			if (!szLine[i] && !szLine[i+1]) break;
			c = szLine[i+1];
			szLine[i+1] = szLine[i];
			szLine[i] = c;
			i+=2;
		}
	}
	sptr = (u16 *)szLine;
	i = gf_utf8_wcstombs(szLineConv, 2048, (const unsigned short **) &sptr);
	if (i == GF_UTF8_FAIL) i = 0;
	szLineConv[i] = 0;
	strcpy(szLine, szLineConv);
	/*this is ugly indeed: since input is UTF16-LE, there are many chances the gf_fgets never reads the \0 after a \n*/
	if (unicode_type==3) gf_fgetc(txt_in);
	return sOK;
}