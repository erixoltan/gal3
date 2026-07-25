/* ggencode.c — order-preserving subscript tuple encoding.
 *
 * Number encoding (canonic numbers only):
 *   value normalized as 0.d1d2...dn x 10^E with d1 != 0, no trailing zeros.
 *   positive:  GG_TAG_POS, byte E+64, then one byte per digit (digit+1),
 *              terminator 0x00.
 *   negative:  GG_TAG_NEG, then the positive payload with every byte
 *              complemented (0xFF - b): larger magnitude sorts earlier,
 *              shorter mantissas sort later, exactly reversing the
 *              positive order.
 *   zero:      GG_TAG_ZERO alone.
 * String encoding: GG_TAG_STR, bytes with 0x00 escaped as 0x00 0xFF,
 *   terminator 0x00. Empty string: GG_TAG_EMPTY alone.
 *
 * MUMPS numbers carry up to 18 significant digits and exponents well
 * inside E in [-64, 63], so the biased exponent fits one byte.
 */
#include "ggencode.h"
#include <string.h>

int gg_is_canonic(const char *s, size_t len)
{
    size_t i = 0;
    if (len == 0) return 0;
    if (s[0] == '-') {
        i = 1;
        if (len == 1) return 0;
        if (len == 2 && s[1] == '0') return 0;      /* -0 */
    }
    if (s[i] == '0') {
        /* "0" alone is canonic; "0anything" is not (03, 0.5) */
        return (i + 1 == len && i == 0) ? 1 : 0;
    }
    if (s[i] == '.') {
        /* .digits, not ending in 0, at least one digit */
        i++;
        if (i == len) return 0;
        for (; i < len; i++)
            if (s[i] < '0' || s[i] > '9') return 0;
        return s[len - 1] != '0';
    }
    if (s[i] < '1' || s[i] > '9') return 0;
    for (; i < len && s[i] >= '0' && s[i] <= '9'; i++) ;
    if (i == len) return 1;
    if (s[i] != '.') return 0;
    i++;
    if (i == len) return 0;                          /* trailing dot */
    for (; i < len; i++)
        if (s[i] < '0' || s[i] > '9') return 0;
    return s[len - 1] != '0';
}

/* extract normalized mantissa digits and exponent from a canonic number.
 * digits receives up to 18 chars, *ndig their count, *exp the power such
 * that value = 0.digits x 10^exp. returns sign (-1, 0, +1). */
static int gg_normalize(const char *s, size_t len,
                        char *digits, int *ndig, int *exp)
{
    size_t i = 0;
    int sign = 1, e = 0, n = 0, seen_point = 0, leading = 1;
    if (s[0] == '-') { sign = -1; i = 1; }
    if (len - i == 1 && s[i] == '0') return 0;
    for (; i < len; i++) {
        char c = s[i];
        if (c == '.') { seen_point = 1; continue; }
        if (leading) {
            if (c == '0') { if (seen_point) e--; continue; }
            leading = 0;
        }
        if (n < 18) digits[n++] = c;
        if (!seen_point) e++;
    }
    /* canonic numbers have no trailing zeros, so digits[] is normalized */
    *ndig = n;
    *exp = e;
    return sign;
}

size_t gg_encode_one(const char *s, size_t len, unsigned char *out, size_t cap)
{
    if (len == 0) {
        if (cap < 1) return 0;
        out[0] = GG_TAG_EMPTY;
        return 1;
    }
    if (gg_is_canonic(s, len)) {
        char digits[18];
        int ndig, exp;
        int sign = gg_normalize(s, len, digits, &ndig, &exp);
        if (sign == 0) {
            if (cap < 1) return 0;
            out[0] = GG_TAG_ZERO;
            return 1;
        }
        size_t need = (size_t)(1 + 1 + ndig + 1);
        if (cap < need) return 0;
        unsigned char body[20];
        body[0] = (unsigned char)(exp + 64);
        for (int k = 0; k < ndig; k++)
            body[1 + k] = (unsigned char)(digits[k] - '0' + 1);
        body[1 + ndig] = 0x00;
        if (sign > 0) {
            out[0] = GG_TAG_POS;
            memcpy(out + 1, body, (size_t)(ndig + 2));
        } else {
            out[0] = GG_TAG_NEG;
            for (int k = 0; k < ndig + 2; k++)
                out[1 + k] = (unsigned char)(0xFF - body[k]);
        }
        return need;
    }
    /* string: tag, escaped bytes, 0x00 terminator */
    size_t o = 0;
    if (cap < 2) return 0;
    out[o++] = GG_TAG_STR;
    for (size_t i = 0; i < len; i++) {
        unsigned char c = (unsigned char)s[i];
        if (c == 0x00) {
            if (o + 2 > cap) return 0;
            out[o++] = 0x00;
            out[o++] = 0xFF;
        } else {
            if (o + 1 > cap) return 0;
            out[o++] = c;
        }
    }
    if (o + 1 > cap) return 0;
    out[o++] = 0x00;
    return o;
}

size_t gg_decode_one(const unsigned char *in, size_t inlen,
                     char *out, size_t cap, size_t *sublen)
{
    if (inlen < 1) return 0;
    unsigned char tag = in[0];
    if (tag == GG_TAG_EMPTY) { *sublen = 0; return 1; }
    if (tag == GG_TAG_ZERO) {
        if (cap < 1) return 0;
        out[0] = '0';
        *sublen = 1;
        return 1;
    }
    if (tag == GG_TAG_POS || tag == GG_TAG_NEG) {
        int neg = (tag == GG_TAG_NEG);
        if (inlen < 3) return 0;
        unsigned char eb = neg ? (unsigned char)(0xFF - in[1]) : in[1];
        int exp = (int)eb - 64;
        char digits[19];
        int ndig = 0;
        size_t i = 2;
        for (; i < inlen; i++) {
            unsigned char b = neg ? (unsigned char)(0xFF - in[i]) : in[i];
            if (b == 0x00) break;
            if (ndig >= 18) return 0;
            digits[ndig++] = (char)('0' + b - 1);
        }
        if (i >= inlen) return 0;                    /* no terminator */
        size_t consumed = i + 1;
        /* rebuild canonic text: 0.digits x 10^exp */
        size_t o = 0;
        if (neg) { if (o >= cap) return 0; out[o++] = '-'; }
        if (exp <= 0) {
            if (o >= cap) return 0;
            out[o++] = '.';
            for (int z = 0; z < -exp; z++) {
                if (o >= cap) return 0;
                out[o++] = '0';
            }
            for (int k = 0; k < ndig; k++) {
                if (o >= cap) return 0;
                out[o++] = digits[k];
            }
        } else if (exp >= ndig) {
            for (int k = 0; k < ndig; k++) {
                if (o >= cap) return 0;
                out[o++] = digits[k];
            }
            for (int z = 0; z < exp - ndig; z++) {
                if (o >= cap) return 0;
                out[o++] = '0';
            }
        } else {
            for (int k = 0; k < exp; k++) {
                if (o >= cap) return 0;
                out[o++] = digits[k];
            }
            if (o >= cap) return 0;
            out[o++] = '.';
            for (int k = exp; k < ndig; k++) {
                if (o >= cap) return 0;
                out[o++] = digits[k];
            }
        }
        *sublen = o;
        return consumed;
    }
    if (tag == GG_TAG_STR) {
        size_t o = 0, i = 1;
        while (i < inlen) {
            unsigned char c = in[i];
            if (c == 0x00) {
                if (i + 1 < inlen && in[i + 1] == 0xFF) {
                    if (o >= cap) return 0;
                    out[o++] = '\0';
                    i += 2;
                    continue;
                }
                *sublen = o;
                return i + 1;
            }
            if (o >= cap) return 0;
            out[o++] = (char)c;
            i++;
        }
        return 0;                                    /* unterminated */
    }
    return 0;
}

size_t gg_encode(const char *const *subs, const size_t *lens, int nsubs,
                 unsigned char *out, size_t cap)
{
    size_t o = 0;
    for (int i = 0; i < nsubs; i++) {
        size_t n = gg_encode_one(subs[i], lens[i], out + o, cap - o);
        if (n == 0) return 0;
        o += n;
    }
    return o;
}
