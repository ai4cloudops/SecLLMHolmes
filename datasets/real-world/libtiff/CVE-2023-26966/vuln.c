#include "tiffiop.h"
#ifdef LOGLUV_SUPPORT

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

/*
 * State block for each open TIFF
 * file using LogLuv compression/decompression.
 */
typedef struct logLuvState LogLuvState;

struct logLuvState
{
    int encoder_state; /* 1 if encoder correctly initialized */
    int user_datafmt;  /* user data format */
    int encode_meth;   /* encoding method */
    int pixel_size;    /* bytes per pixel */

    uint8_t *tbuf;    /* translation buffer */
    tmsize_t tbuflen; /* buffer length */
    void (*tfunc)(LogLuvState *, uint8_t *, tmsize_t);

    TIFFVSetMethod vgetparent; /* super-class method */
    TIFFVSetMethod vsetparent; /* super-class method */
};

#define DecoderState(tif) ((LogLuvState *)(tif)->tif_data)
#define EncoderState(tif) ((LogLuvState *)(tif)->tif_data)

#define SGILOGDATAFMT_UNKNOWN -1

#define MINRUN 4 /* minimum run length */

#include "uvcode.h"

#ifndef UVSCALE
#define U_NEU 0.210526316
#define V_NEU 0.473684211
#define UVSCALE 410.
#endif

#ifndef M_LN2
#define M_LN2 0.69314718055994530942
#endif
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#undef log2 /* Conflict with C'99 function */
#define log2(x) ((1. / M_LN2) * log(x))
#undef exp2 /* Conflict with C'99 function */
#define exp2(x) exp(M_LN2 *(x))

static int tiff_itrunc(double x, int m)
{
    if (m == SGILOGENCODE_NODITHER)
        return (int)x;
    /* Silence CoverityScan warning about bad crypto function */
    /* coverity[dont_call] */
    return (int)(x + rand() * (1. / RAND_MAX) - .5);
}

#if !LOGLUV_PUBLIC
static
#endif
    int
    uv_encode(double u, double v, int em) /* encode (u',v') coordinates */
{
    register int vi, ui;

    if (v < UV_VSTART)
        return oog_encode(u, v);
    vi = tiff_itrunc((v - UV_VSTART) * (1. / UV_SQSIZ), em);
    if (vi >= UV_NVS)
        return oog_encode(u, v);
    if (u < uv_row[vi].ustart)
        return oog_encode(u, v);
    ui = tiff_itrunc((u - uv_row[vi].ustart) * (1. / UV_SQSIZ), em);
    if (ui >= uv_row[vi].nus)
        return oog_encode(u, v);

    return (uv_row[vi].ncum + ui);
}

#if !LOGLUV_PUBLIC
static
#endif
    uint32_t
    LogLuv24fromXYZ(float *XYZ, int em)
{
    int Le, Ce;
    double u, v, s;
    /* encode luminance */
    Le = LogL10fromY(XYZ[1], em);
    /* encode color */
    s = XYZ[0] + 15. * XYZ[1] + 3. * XYZ[2];
    if (!Le || s <= 0.)
    {
        u = U_NEU;
        v = V_NEU;
    }
    else
    {
        u = 4. * XYZ[0] / s;
        v = 9. * XYZ[1] / s;
    }
    Ce = uv_encode(u, v, em);
    if (Ce < 0) /* never happens */
        Ce = uv_encode(U_NEU, V_NEU, SGILOGENCODE_NODITHER);
    /* combine encodings */
    return (Le << 14 | Ce);
}

static void Luv24fromXYZ(LogLuvState *sp, uint8_t *op, tmsize_t n)
{
    uint32_t *luv = (uint32_t *)sp->tbuf;
    float *xyz = (float *)op;

    while (n-- > 0)
    {
        *luv++ = LogLuv24fromXYZ(xyz, sp->encode_meth);
        xyz += 3;
    }
}

static void Luv24fromLuv48(LogLuvState *sp, uint8_t *op, tmsize_t n)
{
    uint32_t *luv = (uint32_t *)sp->tbuf;
    int16_t *luv3 = (int16_t *)op;

    while (n-- > 0)
    {
        int Le, Ce;

        if (luv3[0] <= 0)
            Le = 0;
        else if (luv3[0] >= (1 << 12) + 3314)
            Le = (1 << 10) - 1;
        else if (sp->encode_meth == SGILOGENCODE_NODITHER)
            Le = (luv3[0] - 3314) >> 2;
        else
            Le = tiff_itrunc(.25 * (luv3[0] - 3314.), sp->encode_meth);

        Ce = uv_encode((luv3[1] + .5) / (1 << 15), (luv3[2] + .5) / (1 << 15),
                       sp->encode_meth);
        if (Ce < 0) /* never happens */
            Ce = uv_encode(U_NEU, V_NEU, SGILOGENCODE_NODITHER);
        *luv++ = (uint32_t)Le << 14 | Ce;
        luv3 += 3;
    }
}

static int LogLuvSetupEncode(TIFF *tif)
{
    static const char module[] = "LogLuvSetupEncode";
    LogLuvState *sp = EncoderState(tif);
    TIFFDirectory *td = &tif->tif_dir;

    switch (td->td_photometric)
    {
        case PHOTOMETRIC_LOGLUV:
            if (!LogLuvInitState(tif))
                return (0);
            if (td->td_compression == COMPRESSION_SGILOG24)
            {
                tif->tif_encoderow = LogLuvEncode24;
                switch (sp->user_datafmt)
                {
                    case SGILOGDATAFMT_FLOAT:
                        sp->tfunc = Luv24fromXYZ;
                        break;
                    case SGILOGDATAFMT_16BIT:
                        sp->tfunc = Luv24fromLuv48;
                        break;
                    case SGILOGDATAFMT_RAW:
                        break;
                    default:
                        goto notsupported;
                }
            }
            else
            {
                tif->tif_encoderow = LogLuvEncode32;
                switch (sp->user_datafmt)
                {
                    case SGILOGDATAFMT_FLOAT:
                        sp->tfunc = Luv32fromXYZ;
                        break;
                    case SGILOGDATAFMT_16BIT:
                        sp->tfunc = Luv32fromLuv48;
                        break;
                    case SGILOGDATAFMT_RAW:
                        break;
                    default:
                        goto notsupported;
                }
            }
            break;
        case PHOTOMETRIC_LOGL:
            if (!LogL16InitState(tif))
                return (0);
            tif->tif_encoderow = LogL16Encode;
            switch (sp->user_datafmt)
            {
                case SGILOGDATAFMT_FLOAT:
                    sp->tfunc = L16fromY;
                    break;
                case SGILOGDATAFMT_16BIT:
                    break;
                default:
                    goto notsupported;
            }
            break;
        default:
            TIFFErrorExtR(tif, module,
                          "Inappropriate photometric interpretation %" PRIu16
                          " for SGILog compression; %s",
                          td->td_photometric, "must be either LogLUV or LogL");
            return (0);
    }
    sp->encoder_state = 1;
    return (1);
notsupported:
    TIFFErrorExtR(tif, module,
                  "SGILog compression supported only for %s, or raw data",
                  td->td_photometric == PHOTOMETRIC_LOGL ? "Y, L" : "XYZ, Luv");
    return (0);
}

#endif /* LOGLUV_SUPPORT */
