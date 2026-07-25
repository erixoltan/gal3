/* gg.h — galglobals node operations over encoded subscript tuples.
 *
 * The MUMPS global model as an API: a store holds nodes addressed by
 * encoded subscript tuples (ggencode.h), values are byte strings, and
 * the operations are the global primitives:
 *
 *   set / get            write and read one node
 *   data                 $data: 0 none, 1 value, 10 descendants, 11 both
 *   kill                 remove a node and its whole subtree
 *   order                $order: next/previous sibling subscript at the
 *                        tuple's last level (returns the decoded subscript)
 *   increment            $increment: atomic integer bump, canonic value
 *
 * Two planned backends share this contract: the in-memory store (the
 * locals tier, gg_open_mem) and LMDB (the persistent globals tier,
 * gg_open_lmdb — to come). Keys always come from gg_encode, so ordering
 * is MUMPS canonic collation on every backend.
 */
#ifndef GG_H
#define GG_H

#include <stddef.h>

typedef struct gg_store gg_store;

#define GG_OK        0
#define GG_UNDEF   (-1)   /* node has no value */
#define GG_ERR     (-2)   /* capacity or argument problem */
#define GG_END     (-3)   /* order: no further sibling */

gg_store *gg_open_mem(void);
/* LMDB-backed persistent tier: path is a single data file (created as
 * needed). NULL on failure. */
gg_store *gg_open_lmdb(const char *path);
void      gg_close(gg_store *g);

int gg_set(gg_store *g, const unsigned char *key, size_t klen,
           const char *val, size_t vlen);

/* value into out (cap bytes), *vlen set; GG_UNDEF when the node is valueless */
int gg_get(gg_store *g, const unsigned char *key, size_t klen,
           char *out, size_t cap, size_t *vlen);

/* $data: 0, 1, 10 or 11 */
int gg_data(gg_store *g, const unsigned char *key, size_t klen);

/* kill node and descendants */
int gg_kill(gg_store *g, const unsigned char *key, size_t klen);

/* $order over the last subscript of the tuple: prefix is the encoding of
 * the tuple minus its last subscript, sub/sublen the encoded last
 * subscript (empty sublen = 0 means "from the start" / "from the end").
 * dir > 0 forward, dir < 0 reverse. The next sibling's decoded subscript
 * text lands in out. Returns GG_OK or GG_END. */
int gg_order(gg_store *g,
             const unsigned char *prefix, size_t plen,
             const unsigned char *sub, size_t sublen,
             int dir, char *out, size_t cap, size_t *outlen);

/* $increment (integers): adds by to the node's numeric value (missing or
 * non-numeric counts as 0), stores the canonic result, returns it in
 * *result */
int gg_increment(gg_store *g, const unsigned char *key, size_t klen,
                 long long by, long long *result);

#endif
