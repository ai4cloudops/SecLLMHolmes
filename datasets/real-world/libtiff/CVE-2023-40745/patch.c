#include "libport.h"
#include "tif_config.h"

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <ctype.h>

#ifdef HAVE_UNISTD_H
#include <unistd.h>
#endif

#include "tiffio.h"

#ifndef EXIT_SUCCESS
#define EXIT_SUCCESS 0
#endif
#ifndef EXIT_FAILURE
#define EXIT_FAILURE 1
#endif

#define streq(a, b) (strcmp(a, b) == 0)
#define strneq(a, b, n) (strncmp(a, b, n) == 0)

#define TRUE 1
#define FALSE 0

#define DEFAULT_MAX_MALLOC (256 * 1024 * 1024)

/* malloc size limit (in bytes)
 * disabled when set to 0 */
static tmsize_t maxMalloc = DEFAULT_MAX_MALLOC;

static int outtiled = -1;
static uint32_t tilewidth;
static uint32_t tilelength;

static uint16_t config;
static uint16_t compression;
static double max_z_error = 0.0;
static uint16_t predictor;
static int preset;
static uint16_t fillorder;
static uint16_t orientation;
static uint32_t rowsperstrip;
static uint32_t g3opts;
static int ignore = FALSE; /* if true, ignore read errors */
static uint32_t defg3opts = (uint32_t)-1;
static int quality = 75; /* JPEG quality */
static int jpegcolormode = JPEGCOLORMODE_RGB;
static uint16_t defcompression = (uint16_t)-1;
static uint16_t defpredictor = (uint16_t)-1;
static int defpreset = -1;
static int subcodec = -1;

static int tiffcp(TIFF *, TIFF *);
static int processCompressOptions(char *);
static void usage(int code);

static char comma = ','; /* (default) comma separator character */
static TIFF *bias = NULL;
static int pageNum = 0;
static int pageInSeq = 0;

/**
 * This custom malloc function enforce a maximum allocation size
 */
static void *limitMalloc(tmsize_t s)
{
    if (maxMalloc && (s > maxMalloc))
    {
        fprintf(stderr,
                "MemoryLimitError: allocation of %" TIFF_SSIZE_FORMAT
                " bytes is forbidden. Limit is %" TIFF_SSIZE_FORMAT ".\n",
                s, maxMalloc);
        fprintf(stderr, "                  use -m option to change limit.\n");
        return NULL;
    }
    return _TIFFmalloc(s);
}

int main(int argc, char *argv[])
{
    uint16_t defconfig = (uint16_t)-1;
    uint16_t deffillorder = 0;
    uint32_t deftilewidth = (uint32_t)-1;
    uint32_t deftilelength = (uint32_t)-1;
    uint32_t defrowsperstrip = (uint32_t)0;
    uint64_t diroff = 0;
    TIFF *in;
    TIFF *out;
    char mode[10];
    char *mp = mode;
    int c;
#if !HAVE_DECL_OPTARG
    extern int optind;
    extern char *optarg;
#endif

    *mp++ = 'w';
    *mp = '\0';
    while ((c = getopt(argc, argv, "m:,:b:c:f:l:o:p:r:w:aistBLMC8xh")) != -1)
        switch (c)
        {
            case 'm':
                maxMalloc = (tmsize_t)strtoul(optarg, NULL, 0) << 20;
                break;
            case ',':
                if (optarg[0] != '=')
                    usage(EXIT_FAILURE);
                comma = optarg[1];
                break;
            case 'b': /* this file is bias image subtracted from others */
                if (bias)
                {
                    fputs("Only 1 bias image may be specified\n", stderr);
                    exit(EXIT_FAILURE);
                }
                {
                    uint16_t samples = (uint16_t)-1;
                    char **biasFn = &optarg;
                    bias = openSrcImage(biasFn);
                    if (!bias)
                        exit(EXIT_FAILURE);
                    if (TIFFIsTiled(bias))
                    {
                        fputs("Bias image must be organized in strips\n",
                              stderr);
                        exit(EXIT_FAILURE);
                    }
                    TIFFGetField(bias, TIFFTAG_SAMPLESPERPIXEL, &samples);
                    if (samples != 1)
                    {
                        fputs("Bias image must be monochrome\n", stderr);
                        exit(EXIT_FAILURE);
                    }
                }
                break;
            case 'a': /* append to output */
                mode[0] = 'a';
                break;
            case 'c': /* compression scheme */
                if (!processCompressOptions(optarg))
                    usage(EXIT_FAILURE);
                break;
            case 'f': /* fill order */
                if (streq(optarg, "lsb2msb"))
                    deffillorder = FILLORDER_LSB2MSB;
                else if (streq(optarg, "msb2lsb"))
                    deffillorder = FILLORDER_MSB2LSB;
                else
                    usage(EXIT_FAILURE);
                break;
            case 'i': /* ignore errors */
                ignore = TRUE;
                break;
            case 'l': /* tile length */
                outtiled = TRUE;
                deftilelength = atoi(optarg);
                break;
            case 'o': /* initial directory offset */
                diroff = strtoul(optarg, NULL, 0);
                break;
            case 'p': /* planar configuration */
                if (streq(optarg, "separate"))
                    defconfig = PLANARCONFIG_SEPARATE;
                else if (streq(optarg, "contig"))
                    defconfig = PLANARCONFIG_CONTIG;
                else
                    usage(EXIT_FAILURE);
                break;
            case 'r': /* rows/strip */
                defrowsperstrip = atol(optarg);
                break;
            case 's': /* generate stripped output */
                outtiled = FALSE;
                break;
            case 't': /* generate tiled output */
                outtiled = TRUE;
                break;
            case 'w': /* tile width */
                outtiled = TRUE;
                deftilewidth = atoi(optarg);
                break;
            case 'B':
                if (strlen(mode) < (sizeof(mode) - 1))
                {
                    *mp++ = 'b';
                    *mp = '\0';
                }
                break;
            case 'L':
                if (strlen(mode) < (sizeof(mode) - 1))
                {
                    *mp++ = 'l';
                    *mp = '\0';
                }
                break;
            case 'M':
                if (strlen(mode) < (sizeof(mode) - 1))
                {
                    *mp++ = 'm';
                    *mp = '\0';
                }
                break;
            case 'C':
                if (strlen(mode) < (sizeof(mode) - 1))
                {
                    *mp++ = 'c';
                    *mp = '\0';
                }
                break;
            case '8':
                if (strlen(mode) < (sizeof(mode) - 1))
                {
                    *mp++ = '8';
                    *mp = '\0';
                }
                break;
            case 'x':
                pageInSeq = 1;
                break;
            case 'h':
                usage(EXIT_SUCCESS);
                /*NOTREACHED*/
                break;
            case '?':
                usage(EXIT_FAILURE);
                /*NOTREACHED*/
                break;
        }
    if (argc - optind < 2)
        usage(EXIT_FAILURE);
    TIFFOpenOptions *opts = TIFFOpenOptionsAlloc();
    if (opts == NULL)
    {
        return EXIT_FAILURE;
    }
    TIFFOpenOptionsSetMaxSingleMemAlloc(opts, maxMalloc);
    out = TIFFOpenExt(argv[argc - 1], mode, opts);
    TIFFOpenOptionsFree(opts);
    if (out == NULL)
        return (EXIT_FAILURE);
    if ((argc - optind) == 2)
        pageNum = -1;
    for (; optind < argc - 1; optind++)
    {
        char *imageCursor = argv[optind];
        in = openSrcImage(&imageCursor);
        if (in == NULL)
        {
            (void)TIFFClose(out);
            return (EXIT_FAILURE);
        }
        if (diroff != 0 && !TIFFSetSubDirectory(in, diroff))
        {
            TIFFError(TIFFFileName(in),
                      "Error, setting subdirectory at %" PRIu64, diroff);
            (void)TIFFClose(in);
            (void)TIFFClose(out);
            return (EXIT_FAILURE);
        }
        for (;;)
        {
            config = defconfig;
            compression = defcompression;
            predictor = defpredictor;
            preset = defpreset;
            fillorder = deffillorder;
            rowsperstrip = defrowsperstrip;
            tilewidth = deftilewidth;
            tilelength = deftilelength;
            g3opts = defg3opts;
            if (!tiffcp(in, out) || !TIFFWriteDirectory(out))
            {
                (void)TIFFClose(in);
                (void)TIFFClose(out);
                return (EXIT_FAILURE);
            }
            if (imageCursor)
            { /* seek next image directory */
                if (!nextSrcImage(in, &imageCursor))
                    break;
            }
            else if (!TIFFReadDirectory(in))
                break;
        }
        (void)TIFFClose(in);
    }

    (void)TIFFClose(out);
    return (EXIT_SUCCESS);
}

/* PODD */
static int tiffcp(TIFF *in, TIFF *out)
{
    uint16_t bitspersample = 1, samplesperpixel = 1;
    uint16_t input_compression, input_photometric = PHOTOMETRIC_MINISBLACK;
    copyFunc cf;
    uint32_t width, length;
    const struct cpTag *p;

    CopyField(TIFFTAG_IMAGEWIDTH, width);
    CopyField(TIFFTAG_IMAGELENGTH, length);
    CopyField(TIFFTAG_BITSPERSAMPLE, bitspersample);
    CopyField(TIFFTAG_SAMPLESPERPIXEL, samplesperpixel);
    if (compression != (uint16_t)-1)
        TIFFSetField(out, TIFFTAG_COMPRESSION, compression);
    else
        CopyField(TIFFTAG_COMPRESSION, compression);
    if (!TIFFIsCODECConfigured(compression))
        return FALSE;
    TIFFGetFieldDefaulted(in, TIFFTAG_COMPRESSION, &input_compression);
    TIFFGetFieldDefaulted(in, TIFFTAG_PHOTOMETRIC, &input_photometric);
    if (input_compression == COMPRESSION_JPEG)
    {
        /* Force conversion to RGB */
        TIFFSetField(in, TIFFTAG_JPEGCOLORMODE, JPEGCOLORMODE_RGB);
    }
    else if (input_photometric == PHOTOMETRIC_YCBCR)
    {
        /* Otherwise, can't handle subsampled input */
        uint16_t subsamplinghor, subsamplingver;

        TIFFGetFieldDefaulted(in, TIFFTAG_YCBCRSUBSAMPLING, &subsamplinghor,
                              &subsamplingver);
        if (subsamplinghor != 1 || subsamplingver != 1)
        {
            fprintf(stderr,
                    "tiffcp: %s: Can't copy/convert subsampled image.\n",
                    TIFFFileName(in));
            return FALSE;
        }
    }
    if (compression == COMPRESSION_JPEG)
    {
        if (input_photometric == PHOTOMETRIC_RGB &&
            jpegcolormode == JPEGCOLORMODE_RGB)
            TIFFSetField(out, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_YCBCR);
        else
            TIFFSetField(out, TIFFTAG_PHOTOMETRIC, input_photometric);
    }
    else if (compression == COMPRESSION_SGILOG ||
             compression == COMPRESSION_SGILOG24)
        TIFFSetField(out, TIFFTAG_PHOTOMETRIC,
                     samplesperpixel == 1 ? PHOTOMETRIC_LOGL
                                          : PHOTOMETRIC_LOGLUV);
    else if (input_compression == COMPRESSION_JPEG && samplesperpixel == 3)
    {
        /* RGB conversion was forced above
        hence the output will be of the same type */
        TIFFSetField(out, TIFFTAG_PHOTOMETRIC, PHOTOMETRIC_RGB);
    }
    else
        CopyTag(TIFFTAG_PHOTOMETRIC, 1, TIFF_SHORT);
    if (fillorder != 0)
        TIFFSetField(out, TIFFTAG_FILLORDER, fillorder);
    else
        CopyTag(TIFFTAG_FILLORDER, 1, TIFF_SHORT);
    /*
     * Will copy `Orientation' tag from input image
     */
    TIFFGetFieldDefaulted(in, TIFFTAG_ORIENTATION, &orientation);
    TIFFSetField(out, TIFFTAG_ORIENTATION, orientation);
    /*
     * Choose tiles/strip for the output image according to
     * the command line arguments (-tiles, -strips) and the
     * structure of the input image.
     */
    if (outtiled == -1)
        outtiled = TIFFIsTiled(in);
    if (outtiled)
    {
        /*
         * Setup output file's tile width&height.  If either
         * is not specified, use either the value from the
         * input image or, if nothing is defined, use the
         * library default.
         */
        if (tilewidth == (uint32_t)-1)
            TIFFGetField(in, TIFFTAG_TILEWIDTH, &tilewidth);
        if (tilelength == (uint32_t)-1)
            TIFFGetField(in, TIFFTAG_TILELENGTH, &tilelength);
        TIFFDefaultTileSize(out, &tilewidth, &tilelength);
        TIFFSetField(out, TIFFTAG_TILEWIDTH, tilewidth);
        TIFFSetField(out, TIFFTAG_TILELENGTH, tilelength);
    }
    else
    {
        /*
         * RowsPerStrip is left unspecified: use either the
         * value from the input image or, if nothing is defined,
         * use the library default.
         */
        if (rowsperstrip == (uint32_t)0)
        {
            if (!TIFFGetField(in, TIFFTAG_ROWSPERSTRIP, &rowsperstrip))
            {
                rowsperstrip = TIFFDefaultStripSize(out, rowsperstrip);
            }
            if (rowsperstrip > length && rowsperstrip != (uint32_t)-1)
                rowsperstrip = length;
        }
        else if (rowsperstrip == (uint32_t)-1)
            rowsperstrip = length;
        TIFFSetField(out, TIFFTAG_ROWSPERSTRIP, rowsperstrip);
    }
    if (config != (uint16_t)-1)
        TIFFSetField(out, TIFFTAG_PLANARCONFIG, config);
    else
        CopyField(TIFFTAG_PLANARCONFIG, config);
    if (samplesperpixel <= 4)
        CopyTag(TIFFTAG_TRANSFERFUNCTION, 4, TIFF_SHORT);
    CopyTag(TIFFTAG_COLORMAP, 4, TIFF_SHORT);
    /* SMinSampleValue & SMaxSampleValue */
    switch (compression)
    {
        case COMPRESSION_JPEG:
            TIFFSetField(out, TIFFTAG_JPEGQUALITY, quality);
            TIFFSetField(out, TIFFTAG_JPEGCOLORMODE, jpegcolormode);
            break;
        case COMPRESSION_JBIG:
            CopyTag(TIFFTAG_FAXRECVPARAMS, 1, TIFF_LONG);
            CopyTag(TIFFTAG_FAXRECVTIME, 1, TIFF_LONG);
            CopyTag(TIFFTAG_FAXSUBADDRESS, 1, TIFF_ASCII);
            CopyTag(TIFFTAG_FAXDCS, 1, TIFF_ASCII);
            break;
        case COMPRESSION_LERC:
            if (max_z_error > 0)
            {
                if (TIFFSetField(out, TIFFTAG_LERC_MAXZERROR, max_z_error) != 1)
                {
                    return FALSE;
                }
            }
            if (subcodec != -1)
            {
                if (TIFFSetField(out, TIFFTAG_LERC_ADD_COMPRESSION, subcodec) !=
                    1)
                {
                    return FALSE;
                }
            }
            if (preset != -1)
            {
                switch (subcodec)
                {
                    case LERC_ADD_COMPRESSION_DEFLATE:
                        if (TIFFSetField(out, TIFFTAG_ZIPQUALITY, preset) != 1)
                        {
                            return FALSE;
                        }
                        break;
                    case LERC_ADD_COMPRESSION_ZSTD:
                        if (TIFFSetField(out, TIFFTAG_ZSTD_LEVEL, preset) != 1)
                        {
                            return FALSE;
                        }
                        break;
                }
            }
            break;
        case COMPRESSION_LZW:
        case COMPRESSION_ADOBE_DEFLATE:
        case COMPRESSION_DEFLATE:
        case COMPRESSION_LZMA:
        case COMPRESSION_ZSTD:
            if (predictor != (uint16_t)-1)
                TIFFSetField(out, TIFFTAG_PREDICTOR, predictor);
            else if (input_compression == COMPRESSION_LZW ||
                     input_compression == COMPRESSION_ADOBE_DEFLATE ||
                     input_compression == COMPRESSION_DEFLATE ||
                     input_compression == COMPRESSION_LZMA ||
                     input_compression == COMPRESSION_ZSTD)
            {
                CopyField(TIFFTAG_PREDICTOR, predictor);
            }
            if (compression == COMPRESSION_ADOBE_DEFLATE ||
                compression == COMPRESSION_DEFLATE)
            {
                if (subcodec != -1)
                {
                    if (TIFFSetField(out, TIFFTAG_DEFLATE_SUBCODEC, subcodec) !=
                        1)
                    {
                        return FALSE;
                    }
                }
            }
            /*fallthrough*/
        case COMPRESSION_WEBP:
            if (preset != -1)
            {
                if (preset == 100)
                {
                    TIFFSetField(out, TIFFTAG_WEBP_LOSSLESS, TRUE);
                }
                else
                {
                    TIFFSetField(out, TIFFTAG_WEBP_LEVEL, preset);
                }
            }
            break;
        case COMPRESSION_CCITTFAX3:
        case COMPRESSION_CCITTFAX4:
            if (compression == COMPRESSION_CCITTFAX3)
            {
                if (g3opts != (uint32_t)-1)
                    TIFFSetField(out, TIFFTAG_GROUP3OPTIONS, g3opts);
                else if (input_compression == COMPRESSION_CCITTFAX3)
                    CopyField(TIFFTAG_GROUP3OPTIONS, g3opts);
            }
            else if (input_compression == COMPRESSION_CCITTFAX4)
                CopyTag(TIFFTAG_GROUP4OPTIONS, 1, TIFF_LONG);
            if (input_compression == COMPRESSION_CCITTFAX3 ||
                input_compression == COMPRESSION_CCITTFAX4)
            {
                CopyTag(TIFFTAG_BADFAXLINES, 1, TIFF_LONG);
                CopyTag(TIFFTAG_CLEANFAXDATA, 1, TIFF_LONG);
                CopyTag(TIFFTAG_CONSECUTIVEBADFAXLINES, 1, TIFF_LONG);
            }
            CopyTag(TIFFTAG_FAXRECVPARAMS, 1, TIFF_LONG);
            CopyTag(TIFFTAG_FAXRECVTIME, 1, TIFF_LONG);
            CopyTag(TIFFTAG_FAXSUBADDRESS, 1, TIFF_ASCII);
            break;
    }
    {
        uint32_t len32;
        void **data;
        if (TIFFGetField(in, TIFFTAG_ICCPROFILE, &len32, &data))
            TIFFSetField(out, TIFFTAG_ICCPROFILE, len32, data);
    }
    {
        uint16_t ninks;
        const char *inknames;
        if (TIFFGetField(in, TIFFTAG_NUMBEROFINKS, &ninks))
        {
            TIFFSetField(out, TIFFTAG_NUMBEROFINKS, ninks);
            if (TIFFGetField(in, TIFFTAG_INKNAMES, &inknames))
            {
                int inknameslen = strlen(inknames) + 1;
                const char *cp = inknames;
                while (ninks > 1)
                {
                    cp = strchr(cp, '\0');
                    cp++;
                    inknameslen += (strlen(cp) + 1);
                    ninks--;
                }
                TIFFSetField(out, TIFFTAG_INKNAMES, inknameslen, inknames);
            }
        }
    }
    {
        unsigned short pg0, pg1;

        if (pageInSeq == 1)
        {
            if (pageNum < 0) /* only one input file */
            {
                if (TIFFGetField(in, TIFFTAG_PAGENUMBER, &pg0, &pg1))
                    TIFFSetField(out, TIFFTAG_PAGENUMBER, pg0, pg1);
            }
            else
                TIFFSetField(out, TIFFTAG_PAGENUMBER, pageNum++, 0);
        }
        else
        {
            if (TIFFGetField(in, TIFFTAG_PAGENUMBER, &pg0, &pg1))
            {
                if (pageNum < 0) /* only one input file */
                    TIFFSetField(out, TIFFTAG_PAGENUMBER, pg0, pg1);
                else
                    TIFFSetField(out, TIFFTAG_PAGENUMBER, pageNum++, 0);
            }
        }
    }

    for (p = tags; p < &tags[NTAGS]; p++)
        CopyTag(p->tag, p->count, p->type);

    cf = pickCopyFunc(in, out, bitspersample, samplesperpixel);
    return (cf ? (*cf)(in, out, length, width, samplesperpixel) : FALSE);
}

static void cpStripToTile(uint8_t *out, uint8_t *in, uint32_t rows,
                          uint32_t cols, int outskew, int64_t inskew)
{
    while (rows-- > 0)
    {
        uint32_t j = cols;
        while (j-- > 0)
            *out++ = *in++;
        out += outskew;
        in += inskew;
    }
}

DECLAREreadFunc(readSeparateTilesIntoBuffer)
{
    int status = 1;
    uint32_t imagew = TIFFRasterScanlineSize(in);
    uint32_t tilew = TIFFTileRowSize(in);
    int iskew;
    tsize_t tilesize = TIFFTileSize(in);
    tdata_t tilebuf;
    uint8_t *bufp = (uint8_t *)buf;
    uint32_t tw, tl;
    uint32_t row;
    uint16_t bps = 0, bytes_per_sample;

    if (tilew && spp > (INT_MAX / tilew))
    {
        TIFFError(TIFFFileName(in),
                  "Error, cannot handle that much samples per tile row (Tile "
                  "Width * Samples/Pixel)");
        return 0;
    }

    iskew = imagew - tilew * spp;
    if ( iskew > INT_MAX ){
        TIFFError(TIFFFileName(in),
                  "Error, image raster scan line size is too large");
        return 0;       
    } 
    tilebuf = limitMalloc(tilesize);
    if (tilebuf == 0)
        return 0;
    _TIFFmemset(tilebuf, 0, tilesize);
    (void)TIFFGetField(in, TIFFTAG_TILEWIDTH, &tw);
    (void)TIFFGetField(in, TIFFTAG_TILELENGTH, &tl);
    (void)TIFFGetField(in, TIFFTAG_BITSPERSAMPLE, &bps);
    if (bps == 0)
    {
        TIFFError(TIFFFileName(in), "Error, cannot read BitsPerSample");
        status = 0;
        goto done;
    }
    if ((bps % 8) != 0)
    {
        TIFFError(
            TIFFFileName(in),
            "Error, cannot handle BitsPerSample that is not a multiple of 8");
        status = 0;
        goto done;
    }
    bytes_per_sample = bps / 8;

    for (row = 0; row < imagelength; row += tl)
    {
        uint32_t nrow = (row + tl > imagelength) ? imagelength - row : tl;
        uint32_t colb = 0;
        uint32_t col;

        for (col = 0; col < imagewidth; col += tw)
        {
            tsample_t s;

            for (s = 0; s < spp; s++)
            {
                if (TIFFReadTile(in, tilebuf, col, row, 0, s) < 0 && !ignore)
                {
                    TIFFError(TIFFFileName(in),
                              "Error, can't read tile at %" PRIu32 " %" PRIu32
                              ", "
                              "sample %" PRIu16,
                              col, row, s);
                    status = 0;
                    goto done;
                }
                /*
                 * Tile is clipped horizontally.  Calculate
                 * visible portion and skewing factors.
                 */
                if (colb + tilew * spp > imagew)
                {
                    uint32_t width = imagew - colb;
                    int oskew = tilew * spp - width;
                    cpSeparateBufToContigBuf(
                        bufp + colb + s * bytes_per_sample, tilebuf, nrow,
                        width / (spp * bytes_per_sample), oskew + iskew,
                        oskew / spp, spp, bytes_per_sample);
                }
                else
                    cpSeparateBufToContigBuf(bufp + colb + s * bytes_per_sample,
                                             tilebuf, nrow, tw, iskew, 0, spp,
                                             bytes_per_sample);
            }
            colb += tilew * spp;
        }
        bufp += imagew * nrow;
    }
done:
    _TIFFfree(tilebuf);
    return status;
}

DECLAREwriteFunc(writeBufferToContigTiles)
{
    uint32_t imagew = TIFFScanlineSize(out);
    uint32_t tilew = TIFFTileRowSize(out);
    int iskew = imagew - tilew;
    tsize_t tilesize = TIFFTileSize(out);
    tdata_t obuf;
    uint8_t *bufp = (uint8_t *)buf;
    uint32_t tl, tw;
    uint32_t row;

    (void)spp;

    obuf = limitMalloc(TIFFTileSize(out));
    if (obuf == NULL)
        return 0;
    _TIFFmemset(obuf, 0, tilesize);
    (void)TIFFGetField(out, TIFFTAG_TILELENGTH, &tl);
    (void)TIFFGetField(out, TIFFTAG_TILEWIDTH, &tw);
    for (row = 0; row < imagelength; row += tilelength)
    {
        uint32_t nrow = (row + tl > imagelength) ? imagelength - row : tl;
        uint32_t colb = 0;
        uint32_t col;

        for (col = 0; col < imagewidth && colb < imagew; col += tw)
        {
            /*
             * Tile is clipped horizontally.  Calculate
             * visible portion and skewing factors.
             */
            if (colb + tilew > imagew)
            {
                uint32_t width = imagew - colb;
                int oskew = tilew - width;
                cpStripToTile(obuf, bufp + colb, nrow, width, oskew,
                              oskew + iskew);
            }
            else
                cpStripToTile(obuf, bufp + colb, nrow, tilew, 0, iskew);
            if (TIFFWriteTile(out, obuf, col, row, 0, 0) < 0)
            {
                TIFFError(TIFFFileName(out),
                          "Error, can't write tile at %" PRIu32 " %" PRIu32,
                          col, row);
                _TIFFfree(obuf);
                return 0;
            }
            colb += tilew;
        }
        bufp += nrow * imagew;
    }
    _TIFFfree(obuf);
    return 1;
}
