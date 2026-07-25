/* ggencode.h — order-preserving subscript tuple encoding for galglobals.
 *
 * Encodes MUMPS-style subscript tuples into byte strings whose bytewise
 * (memcmp) order equals MUMPS canonic collation:
 *
 *   ""  <  numbers (numeric order, negatives first)  <  strings (byte order)
 *
 * A subscript that is a canonic number ("7", "-1.5", ".5", "0") collates
 * numerically; any other text ("07", "0.5", "abc") collates as a string.
 * Each encoded subscript is self-terminating and prefix-free, so tuple
 * encodings concatenate and memcmp gives node ordering; a tuple is a strict
 * prefix of its descendants, which is what $order/$data walks need.
 */
#ifndef GGENCODE_H
#define GGENCODE_H

#include <stddef.h>

/* type tags — relative order is the collation order */
#define GG_TAG_EMPTY 0x05
#define GG_TAG_NEG   0x10
#define GG_TAG_ZERO  0x15
#define GG_TAG_POS   0x1A
#define GG_TAG_STR   0x20

/* returns 1 if s[0..len) is a canonic MUMPS number, else 0 */
int gg_is_canonic(const char *s, size_t len);

/* encode one subscript; returns bytes written, or 0 if cap too small */
size_t gg_encode_one(const char *s, size_t len, unsigned char *out, size_t cap);

/* decode one subscript starting at in[0..inlen); writes the subscript text
 * to out (cap bytes), sets *sublen, returns bytes consumed or 0 on error */
size_t gg_decode_one(const unsigned char *in, size_t inlen,
                     char *out, size_t cap, size_t *sublen);

/* encode a whole tuple (nsubs subscripts); returns total bytes or 0 */
size_t gg_encode(const char *const *subs, const size_t *lens, int nsubs,
                 unsigned char *out, size_t cap);

#endif
