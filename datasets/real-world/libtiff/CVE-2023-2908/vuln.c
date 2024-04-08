#include "tiffiop.h"
#include <float.h> /*--: for Rational2Double */
#include <limits.h>

/*
 * These are used in the backwards compatibility code...
 */
#define DATATYPE_VOID 0   /* !untyped data */
#define DATATYPE_INT 1    /* !signed integer data */
#define DATATYPE_UINT 2   /* !unsigned integer data */
#define DATATYPE_IEEEFP 3 /* !IEEE floating point data */

static void setByteArray(TIFF *tif, void **vpp, const void *vp, size_t nmemb,
                         size_t elem_size)
{
    if (*vpp)
    {
        _TIFFfreeExt(tif, *vpp);
        *vpp = 0;
    }
    if (vp)
    {
        tmsize_t bytes = _TIFFMultiplySSize(NULL, nmemb, elem_size, NULL);
        if (bytes)
            *vpp = (void *)_TIFFmallocExt(tif, bytes);
        if (*vpp)
            _TIFFmemcpy(*vpp, vp, bytes);
    }
}

static void _TIFFsetNString(TIFF *tif, char **cpp, const char *cp, uint32_t n)
{
    setByteArray(tif, (void **)cpp, cp, n, 1);
}
void _TIFFsetShortArray(uint16_t **wpp, const uint16_t *wp, uint32_t n)
{
    setByteArray(NULL, (void **)wpp, wp, n, sizeof(uint16_t));
}
void _TIFFsetShortArrayExt(TIFF *tif, uint16_t **wpp, const uint16_t *wp,
                           uint32_t n)
{
    setByteArray(tif, (void **)wpp, wp, n, sizeof(uint16_t));
}
static void _TIFFsetLong8Array(TIFF *tif, uint64_t **lpp, const uint64_t *lp,
                               uint32_t n)
{
    setByteArray(tif, (void **)lpp, lp, n, sizeof(uint64_t));
}
void _TIFFsetFloatArrayExt(TIFF *tif, float **fpp, const float *fp, uint32_t n)
{
    setByteArray(tif, (void **)fpp, fp, n, sizeof(float));
}
void _TIFFsetDoubleArrayExt(TIFF *tif, double **dpp, const double *dp,
                            uint32_t n)
{
    setByteArray(tif, (void **)dpp, dp, n, sizeof(double));
}
static void setDoubleArrayOneValue(TIFF *tif, double **vpp, double value,
                                   size_t nmemb)
{
    if (*vpp)
        _TIFFfreeExt(tif, *vpp);
    *vpp = _TIFFmallocExt(tif, nmemb * sizeof(double));
    if (*vpp)
    {
        while (nmemb--)
            ((double *)*vpp)[nmemb] = value;
    }
}

/*
 * Install extra samples information.
 */
static int setExtraSamples(TIFF *tif, va_list ap, uint32_t *v)
{
/* XXX: Unassociated alpha data == 999 is a known Corel Draw bug, see below */
#define EXTRASAMPLE_COREL_UNASSALPHA 999

    uint16_t *va;
    uint32_t i;
    TIFFDirectory *td = &tif->tif_dir;
    static const char module[] = "setExtraSamples";

    *v = (uint16_t)va_arg(ap, uint16_vap);
    if ((uint16_t)*v > td->td_samplesperpixel)
        return 0;
    va = va_arg(ap, uint16_t *);
    if (*v > 0 && va == NULL) /* typically missing param */
        return 0;
    for (i = 0; i < *v; i++)
    {
        if (va[i] > EXTRASAMPLE_UNASSALPHA)
        {
            /*
             * XXX: Corel Draw is known to produce incorrect
             * ExtraSamples tags which must be patched here if we
             * want to be able to open some of the damaged TIFF
             * files:
             */
            if (va[i] == EXTRASAMPLE_COREL_UNASSALPHA)
                va[i] = EXTRASAMPLE_UNASSALPHA;
            else
                return 0;
        }
    }

    if (td->td_transferfunction[0] != NULL &&
        (td->td_samplesperpixel - *v > 1) &&
        !(td->td_samplesperpixel - td->td_extrasamples > 1))
    {
        TIFFWarningExtR(tif, module,
                        "ExtraSamples tag value is changing, "
                        "but TransferFunction was read with a different value. "
                        "Canceling it");
        TIFFClrFieldBit(tif, FIELD_TRANSFERFUNCTION);
        _TIFFfreeExt(tif, td->td_transferfunction[0]);
        td->td_transferfunction[0] = NULL;
    }

    td->td_extrasamples = (uint16_t)*v;
    _TIFFsetShortArrayExt(tif, &td->td_sampleinfo, va, td->td_extrasamples);
    return 1;

#undef EXTRASAMPLE_COREL_UNASSALPHA
}

static uint16_t countInkNamesString(TIFF *tif, uint32_t slen, const char *s)
{
    uint16_t i = 0;
    const char *ep = s + slen;
    const char *cp = s;

    if (slen > 0)
    {
        do
        {
            for (; cp < ep && *cp != '\0'; cp++)
            {
            }
            if (cp >= ep)
                goto bad;
            cp++; /* skip \0 */
            i++;
        } while (cp < ep);
        return (i);
    }
bad:
    TIFFErrorExtR(tif, "TIFFSetField",
                  "%s: Invalid InkNames value; no NUL at given buffer end "
                  "location %" PRIu32 ", after %" PRIu16 " ink",
                  tif->tif_name, slen, i);
    return (0);
}

static int _TIFFVSetField(TIFF *tif, uint32_t tag, va_list ap)
{
    static const char module[] = "_TIFFVSetField";

    TIFFDirectory *td = &tif->tif_dir;
    int status = 1;
    uint32_t v32, v;
    double dblval;
    char *s;
    const TIFFField *fip = TIFFFindField(tif, tag, TIFF_ANY);
    uint32_t standard_tag = tag;
    if (fip == NULL) /* cannot happen since OkToChangeTag() already checks it */
        return 0;
    /*
     * We want to force the custom code to be used for custom
     * fields even if the tag happens to match a well known
     * one - important for reinterpreted handling of standard
     * tag values in custom directories (i.e. EXIF)
     */
    if (fip->field_bit == FIELD_CUSTOM)
    {
        standard_tag = 0;
    }

    switch (standard_tag)
    {
        case TIFFTAG_SUBFILETYPE:
            td->td_subfiletype = (uint32_t)va_arg(ap, uint32_t);
            break;
        case TIFFTAG_IMAGEWIDTH:
            td->td_imagewidth = (uint32_t)va_arg(ap, uint32_t);
            break;
        case TIFFTAG_IMAGELENGTH:
            td->td_imagelength = (uint32_t)va_arg(ap, uint32_t);
            break;
        case TIFFTAG_BITSPERSAMPLE:
            td->td_bitspersample = (uint16_t)va_arg(ap, uint16_vap);
            /*
             * If the data require post-decoding processing to byte-swap
             * samples, set it up here.  Note that since tags are required
             * to be ordered, compression code can override this behavior
             * in the setup method if it wants to roll the post decoding
             * work in with its normal work.
             */
            if (tif->tif_flags & TIFF_SWAB)
            {
                if (td->td_bitspersample == 8)
                    tif->tif_postdecode = _TIFFNoPostDecode;
                else if (td->td_bitspersample == 16)
                    tif->tif_postdecode = _TIFFSwab16BitData;
                else if (td->td_bitspersample == 24)
                    tif->tif_postdecode = _TIFFSwab24BitData;
                else if (td->td_bitspersample == 32)
                    tif->tif_postdecode = _TIFFSwab32BitData;
                else if (td->td_bitspersample == 64)
                    tif->tif_postdecode = _TIFFSwab64BitData;
                else if (td->td_bitspersample == 128) /* two 64's */
                    tif->tif_postdecode = _TIFFSwab64BitData;
            }
            break;
        case TIFFTAG_COMPRESSION:
            v = (uint16_t)va_arg(ap, uint16_vap);
            /*
             * If we're changing the compression scheme, notify the
             * previous module so that it can cleanup any state it's
             * setup.
             */
            if (TIFFFieldSet(tif, FIELD_COMPRESSION))
            {
                if ((uint32_t)td->td_compression == v)
                    break;
                (*tif->tif_cleanup)(tif);
                tif->tif_flags &= ~TIFF_CODERSETUP;
            }
            /*
             * Setup new compression routine state.
             */
            if ((status = TIFFSetCompressionScheme(tif, v)) != 0)
                td->td_compression = (uint16_t)v;
            else
                status = 0;
            break;
        case TIFFTAG_PHOTOMETRIC:
            td->td_photometric = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_THRESHHOLDING:
            td->td_threshholding = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_FILLORDER:
            v = (uint16_t)va_arg(ap, uint16_vap);
            if (v != FILLORDER_LSB2MSB && v != FILLORDER_MSB2LSB)
                goto badvalue;
            td->td_fillorder = (uint16_t)v;
            break;
        case TIFFTAG_ORIENTATION:
            v = (uint16_t)va_arg(ap, uint16_vap);
            if (v < ORIENTATION_TOPLEFT || ORIENTATION_LEFTBOT < v)
                goto badvalue;
            else
                td->td_orientation = (uint16_t)v;
            break;
        case TIFFTAG_SAMPLESPERPIXEL:
            v = (uint16_t)va_arg(ap, uint16_vap);
            if (v == 0)
                goto badvalue;
            if (v != td->td_samplesperpixel)
            {
                /* See http://bugzilla.maptools.org/show_bug.cgi?id=2500 */
                if (td->td_sminsamplevalue != NULL)
                {
                    TIFFWarningExtR(tif, module,
                                    "SamplesPerPixel tag value is changing, "
                                    "but SMinSampleValue tag was read with a "
                                    "different value. Canceling it");
                    TIFFClrFieldBit(tif, FIELD_SMINSAMPLEVALUE);
                    _TIFFfreeExt(tif, td->td_sminsamplevalue);
                    td->td_sminsamplevalue = NULL;
                }
                if (td->td_smaxsamplevalue != NULL)
                {
                    TIFFWarningExtR(tif, module,
                                    "SamplesPerPixel tag value is changing, "
                                    "but SMaxSampleValue tag was read with a "
                                    "different value. Canceling it");
                    TIFFClrFieldBit(tif, FIELD_SMAXSAMPLEVALUE);
                    _TIFFfreeExt(tif, td->td_smaxsamplevalue);
                    td->td_smaxsamplevalue = NULL;
                }
                /* Test if 3 transfer functions instead of just one are now
                   needed See http://bugzilla.maptools.org/show_bug.cgi?id=2820
                 */
                if (td->td_transferfunction[0] != NULL &&
                    (v - td->td_extrasamples > 1) &&
                    !(td->td_samplesperpixel - td->td_extrasamples > 1))
                {
                    TIFFWarningExtR(tif, module,
                                    "SamplesPerPixel tag value is changing, "
                                    "but TransferFunction was read with a "
                                    "different value. Canceling it");
                    TIFFClrFieldBit(tif, FIELD_TRANSFERFUNCTION);
                    _TIFFfreeExt(tif, td->td_transferfunction[0]);
                    td->td_transferfunction[0] = NULL;
                }
            }
            td->td_samplesperpixel = (uint16_t)v;
            break;
        case TIFFTAG_ROWSPERSTRIP:
            v32 = (uint32_t)va_arg(ap, uint32_t);
            if (v32 == 0)
                goto badvalue32;
            td->td_rowsperstrip = v32;
            if (!TIFFFieldSet(tif, FIELD_TILEDIMENSIONS))
            {
                td->td_tilelength = v32;
                td->td_tilewidth = td->td_imagewidth;
            }
            break;
        case TIFFTAG_MINSAMPLEVALUE:
            td->td_minsamplevalue = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_MAXSAMPLEVALUE:
            td->td_maxsamplevalue = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_SMINSAMPLEVALUE:
            if (tif->tif_flags & TIFF_PERSAMPLE)
                _TIFFsetDoubleArrayExt(tif, &td->td_sminsamplevalue,
                                       va_arg(ap, double *),
                                       td->td_samplesperpixel);
            else
                setDoubleArrayOneValue(tif, &td->td_sminsamplevalue,
                                       va_arg(ap, double),
                                       td->td_samplesperpixel);
            break;
        case TIFFTAG_SMAXSAMPLEVALUE:
            if (tif->tif_flags & TIFF_PERSAMPLE)
                _TIFFsetDoubleArrayExt(tif, &td->td_smaxsamplevalue,
                                       va_arg(ap, double *),
                                       td->td_samplesperpixel);
            else
                setDoubleArrayOneValue(tif, &td->td_smaxsamplevalue,
                                       va_arg(ap, double),
                                       td->td_samplesperpixel);
            break;
        case TIFFTAG_XRESOLUTION:
            dblval = va_arg(ap, double);
            if (dblval != dblval || dblval < 0)
                goto badvaluedouble;
            td->td_xresolution = _TIFFClampDoubleToFloat(dblval);
            break;
        case TIFFTAG_YRESOLUTION:
            dblval = va_arg(ap, double);
            if (dblval != dblval || dblval < 0)
                goto badvaluedouble;
            td->td_yresolution = _TIFFClampDoubleToFloat(dblval);
            break;
        case TIFFTAG_PLANARCONFIG:
            v = (uint16_t)va_arg(ap, uint16_vap);
            if (v != PLANARCONFIG_CONTIG && v != PLANARCONFIG_SEPARATE)
                goto badvalue;
            td->td_planarconfig = (uint16_t)v;
            break;
        case TIFFTAG_XPOSITION:
            td->td_xposition = _TIFFClampDoubleToFloat(va_arg(ap, double));
            break;
        case TIFFTAG_YPOSITION:
            td->td_yposition = _TIFFClampDoubleToFloat(va_arg(ap, double));
            break;
        case TIFFTAG_RESOLUTIONUNIT:
            v = (uint16_t)va_arg(ap, uint16_vap);
            if (v < RESUNIT_NONE || RESUNIT_CENTIMETER < v)
                goto badvalue;
            td->td_resolutionunit = (uint16_t)v;
            break;
        case TIFFTAG_PAGENUMBER:
            td->td_pagenumber[0] = (uint16_t)va_arg(ap, uint16_vap);
            td->td_pagenumber[1] = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_HALFTONEHINTS:
            td->td_halftonehints[0] = (uint16_t)va_arg(ap, uint16_vap);
            td->td_halftonehints[1] = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_COLORMAP:
            v32 = (uint32_t)(1L << td->td_bitspersample);
            _TIFFsetShortArrayExt(tif, &td->td_colormap[0],
                                  va_arg(ap, uint16_t *), v32);
            _TIFFsetShortArrayExt(tif, &td->td_colormap[1],
                                  va_arg(ap, uint16_t *), v32);
            _TIFFsetShortArrayExt(tif, &td->td_colormap[2],
                                  va_arg(ap, uint16_t *), v32);
            break;
        case TIFFTAG_EXTRASAMPLES:
            if (!setExtraSamples(tif, ap, &v))
                goto badvalue;
            break;
        case TIFFTAG_MATTEING:
            td->td_extrasamples = (((uint16_t)va_arg(ap, uint16_vap)) != 0);
            if (td->td_extrasamples)
            {
                uint16_t sv = EXTRASAMPLE_ASSOCALPHA;
                _TIFFsetShortArrayExt(tif, &td->td_sampleinfo, &sv, 1);
            }
            break;
        case TIFFTAG_TILEWIDTH:
            v32 = (uint32_t)va_arg(ap, uint32_t);
            if (v32 % 16)
            {
                if (tif->tif_mode != O_RDONLY)
                    goto badvalue32;
                TIFFWarningExtR(
                    tif, tif->tif_name,
                    "Nonstandard tile width %" PRIu32 ", convert file", v32);
            }
            td->td_tilewidth = v32;
            tif->tif_flags |= TIFF_ISTILED;
            break;
        case TIFFTAG_TILELENGTH:
            v32 = (uint32_t)va_arg(ap, uint32_t);
            if (v32 % 16)
            {
                if (tif->tif_mode != O_RDONLY)
                    goto badvalue32;
                TIFFWarningExtR(
                    tif, tif->tif_name,
                    "Nonstandard tile length %" PRIu32 ", convert file", v32);
            }
            td->td_tilelength = v32;
            tif->tif_flags |= TIFF_ISTILED;
            break;
        case TIFFTAG_TILEDEPTH:
            v32 = (uint32_t)va_arg(ap, uint32_t);
            if (v32 == 0)
                goto badvalue32;
            td->td_tiledepth = v32;
            break;
        case TIFFTAG_DATATYPE:
            v = (uint16_t)va_arg(ap, uint16_vap);
            switch (v)
            {
                case DATATYPE_VOID:
                    v = SAMPLEFORMAT_VOID;
                    break;
                case DATATYPE_INT:
                    v = SAMPLEFORMAT_INT;
                    break;
                case DATATYPE_UINT:
                    v = SAMPLEFORMAT_UINT;
                    break;
                case DATATYPE_IEEEFP:
                    v = SAMPLEFORMAT_IEEEFP;
                    break;
                default:
                    goto badvalue;
            }
            td->td_sampleformat = (uint16_t)v;
            break;
        case TIFFTAG_SAMPLEFORMAT:
            v = (uint16_t)va_arg(ap, uint16_vap);
            if (v < SAMPLEFORMAT_UINT || SAMPLEFORMAT_COMPLEXIEEEFP < v)
                goto badvalue;
            td->td_sampleformat = (uint16_t)v;

            /*  Try to fix up the SWAB function for complex data. */
            if (td->td_sampleformat == SAMPLEFORMAT_COMPLEXINT &&
                td->td_bitspersample == 32 &&
                tif->tif_postdecode == _TIFFSwab32BitData)
                tif->tif_postdecode = _TIFFSwab16BitData;
            else if ((td->td_sampleformat == SAMPLEFORMAT_COMPLEXINT ||
                      td->td_sampleformat == SAMPLEFORMAT_COMPLEXIEEEFP) &&
                     td->td_bitspersample == 64 &&
                     tif->tif_postdecode == _TIFFSwab64BitData)
                tif->tif_postdecode = _TIFFSwab32BitData;
            break;
        case TIFFTAG_IMAGEDEPTH:
            td->td_imagedepth = (uint32_t)va_arg(ap, uint32_t);
            break;
        case TIFFTAG_SUBIFD:
            if ((tif->tif_flags & TIFF_INSUBIFD) == 0)
            {
                td->td_nsubifd = (uint16_t)va_arg(ap, uint16_vap);
                _TIFFsetLong8Array(tif, &td->td_subifd,
                                   (uint64_t *)va_arg(ap, uint64_t *),
                                   (uint32_t)td->td_nsubifd);
            }
            else
            {
                TIFFErrorExtR(tif, module, "%s: Sorry, cannot nest SubIFDs",
                              tif->tif_name);
                status = 0;
            }
            break;
        case TIFFTAG_YCBCRPOSITIONING:
            td->td_ycbcrpositioning = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_YCBCRSUBSAMPLING:
            td->td_ycbcrsubsampling[0] = (uint16_t)va_arg(ap, uint16_vap);
            td->td_ycbcrsubsampling[1] = (uint16_t)va_arg(ap, uint16_vap);
            break;
        case TIFFTAG_TRANSFERFUNCTION:
        {
            uint32_t i;
            v = (td->td_samplesperpixel - td->td_extrasamples) > 1 ? 3 : 1;
            for (i = 0; i < v; i++)
                _TIFFsetShortArrayExt(tif, &td->td_transferfunction[i],
                                      va_arg(ap, uint16_t *),
                                      1U << td->td_bitspersample);
            break;
        }
        case TIFFTAG_REFERENCEBLACKWHITE:
            /* XXX should check for null range */
            _TIFFsetFloatArrayExt(tif, &td->td_refblackwhite,
                                  va_arg(ap, float *), 6);
            break;
        case TIFFTAG_INKNAMES:
        {
            v = (uint16_t)va_arg(ap, uint16_vap);
            s = va_arg(ap, char *);
            uint16_t ninksinstring;
            ninksinstring = countInkNamesString(tif, v, s);
            status = ninksinstring > 0;
            if (ninksinstring > 0)
            {
                _TIFFsetNString(tif, &td->td_inknames, s, v);
                td->td_inknameslen = v;
                /* Set NumberOfInks to the value ninksinstring */
                if (TIFFFieldSet(tif, FIELD_NUMBEROFINKS))
                {
                    if (td->td_numberofinks != ninksinstring)
                    {
                        TIFFErrorExtR(
                            tif, module,
                            "Warning %s; Tag %s:\n  Value %" PRIu16
                            " of NumberOfInks is different from the number of "
                            "inks %" PRIu16
                            ".\n  -> NumberOfInks value adapted to %" PRIu16 "",
                            tif->tif_name, fip->field_name, td->td_numberofinks,
                            ninksinstring, ninksinstring);
                        td->td_numberofinks = ninksinstring;
                    }
                }
                else
                {
                    td->td_numberofinks = ninksinstring;
                    TIFFSetFieldBit(tif, FIELD_NUMBEROFINKS);
                }
                if (TIFFFieldSet(tif, FIELD_SAMPLESPERPIXEL))
                {
                    if (td->td_numberofinks != td->td_samplesperpixel)
                    {
                        TIFFErrorExtR(tif, module,
                                      "Warning %s; Tag %s:\n  Value %" PRIu16
                                      " of NumberOfInks is different from the "
                                      "SamplesPerPixel value %" PRIu16 "",
                                      tif->tif_name, fip->field_name,
                                      td->td_numberofinks,
                                      td->td_samplesperpixel);
                    }
                }
            }
        }
        break;
    }
    if (status)
    {
        const TIFFField *fip2 = TIFFFieldWithTag(tif, tag);
        if (fip2)
            TIFFSetFieldBit(tif, fip2->field_bit);
        tif->tif_flags |= TIFF_DIRTYDIRECT;
    }

end:
    va_end(ap);
    return (status);
badvalue:
{
    const TIFFField *fip2 = TIFFFieldWithTag(tif, tag);
    TIFFErrorExtR(tif, module, "%s: Bad value %" PRIu32 " for \"%s\" tag",
                  tif->tif_name, v, fip2 ? fip2->field_name : "Unknown");
    va_end(ap);
}
    return (0);
badvalue32:
{
    const TIFFField *fip2 = TIFFFieldWithTag(tif, tag);
    TIFFErrorExtR(tif, module, "%s: Bad value %" PRIu32 " for \"%s\" tag",
                  tif->tif_name, v32, fip2 ? fip2->field_name : "Unknown");
    va_end(ap);
}
    return (0);
badvaluedouble:
{
    const TIFFField *fip2 = TIFFFieldWithTag(tif, tag);
    TIFFErrorExtR(tif, module, "%s: Bad value %f for \"%s\" tag", tif->tif_name,
                  dblval, fip2 ? fip2->field_name : "Unknown");
    va_end(ap);
}
    return (0);
badvalueifd8long8:
{
    /* Error message issued already above. */
    TIFFTagValue *tv2 = NULL;
    int iCustom2, iC2;
    /* Find the existing entry for this custom value. */
    for (iCustom2 = 0; iCustom2 < td->td_customValueCount; iCustom2++)
    {
        if (td->td_customValues[iCustom2].info->field_tag == tag)
        {
            tv2 = td->td_customValues + (iCustom2);
            break;
        }
    }
    if (tv2 != NULL)
    {
        /* Remove custom field from custom list */
        if (tv2->value != NULL)
        {
            _TIFFfreeExt(tif, tv2->value);
            tv2->value = NULL;
        }
        /* Shorten list and close gap in customValues list.
         * Re-allocation of td_customValues not necessary here. */
        td->td_customValueCount--;
        for (iC2 = iCustom2; iC2 < td->td_customValueCount; iC2++)
        {
            td->td_customValues[iC2] = td->td_customValues[iC2 + 1];
        }
    }
    else
    {
        assert(0);
    }
    va_end(ap);
}
    return (0);
} /*-- _TIFFVSetField() --*/
