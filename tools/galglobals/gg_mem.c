/* gg_mem.c — the in-memory backend: a sorted array of (key, value) with
 * binary search. Correctness-first (inserts are O(n) memmove); the same
 * contract runs over LMDB for the persistent tier, and a skiplist can
 * replace this if the locals tier ever shows up in a profile.
 *
 * Ordering is plain memcmp on the encoded keys — gg_encode guarantees
 * that equals MUMPS collation, and that a tuple's descendants are
 * exactly the keys it prefixes. */
#include "gg_impl.h"
#include "ggencode.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    unsigned char *key;
    size_t klen;
    char *val;
    size_t vlen;
} gg_node;

typedef struct {
    gg_node *nodes;
    size_t count;
    size_t cap;
} gg_mem;

static int keycmp(const unsigned char *a, size_t alen,
                  const unsigned char *b, size_t blen)
{
    size_t m = alen < blen ? alen : blen;
    int c = memcmp(a, b, m);
    if (c) return c;
    if (alen == blen) return 0;
    return alen < blen ? -1 : 1;
}

/* index of the first node with key >= (key,klen) */
static size_t lower_bound(gg_mem *g, const unsigned char *key, size_t klen)
{
    size_t lo = 0, hi = g->count;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (keycmp(g->nodes[mid].key, g->nodes[mid].klen, key, klen) < 0)
            lo = mid + 1;
        else
            hi = mid;
    }
    return lo;
}

static int is_prefix(const unsigned char *p, size_t plen,
                     const unsigned char *k, size_t klen)
{
    return klen >= plen && memcmp(p, k, plen) == 0;
}

static void mem_close(void *impl)
{
    gg_mem *g = impl;
    if (!g) return;
    for (size_t i = 0; i < g->count; i++) {
        free(g->nodes[i].key);
        free(g->nodes[i].val);
    }
    free(g->nodes);
    free(g);
}

static int mem_set(void *impl, const unsigned char *key, size_t klen,
                   const char *val, size_t vlen)
{
    gg_mem *g = impl;
    size_t at = lower_bound(g, key, klen);
    if (at < g->count &&
        keycmp(g->nodes[at].key, g->nodes[at].klen, key, klen) == 0) {
        char *nv = malloc(vlen ? vlen : 1);
        if (!nv) return GG_ERR;
        memcpy(nv, val, vlen);
        free(g->nodes[at].val);
        g->nodes[at].val = nv;
        g->nodes[at].vlen = vlen;
        return GG_OK;
    }
    if (g->count == g->cap) {
        size_t ncap = g->cap ? g->cap * 2 : 64;
        gg_node *nn = realloc(g->nodes, ncap * sizeof(gg_node));
        if (!nn) return GG_ERR;
        g->nodes = nn;
        g->cap = ncap;
    }
    memmove(g->nodes + at + 1, g->nodes + at,
            (g->count - at) * sizeof(gg_node));
    g->nodes[at].key = malloc(klen ? klen : 1);
    g->nodes[at].val = malloc(vlen ? vlen : 1);
    if (!g->nodes[at].key || !g->nodes[at].val) return GG_ERR;
    memcpy(g->nodes[at].key, key, klen);
    memcpy(g->nodes[at].val, val, vlen);
    g->nodes[at].klen = klen;
    g->nodes[at].vlen = vlen;
    g->count++;
    return GG_OK;
}

static int mem_get(void *impl, const unsigned char *key, size_t klen,
                   char *out, size_t cap, size_t *vlen)
{
    gg_mem *g = impl;
    size_t at = lower_bound(g, key, klen);
    if (at >= g->count ||
        keycmp(g->nodes[at].key, g->nodes[at].klen, key, klen) != 0)
        return GG_UNDEF;
    if (g->nodes[at].vlen > cap) return GG_ERR;
    memcpy(out, g->nodes[at].val, g->nodes[at].vlen);
    *vlen = g->nodes[at].vlen;
    return GG_OK;
}

static int mem_data(void *impl, const unsigned char *key, size_t klen)
{
    gg_mem *g = impl;
    size_t at = lower_bound(g, key, klen);
    int value = 0, kids = 0;
    if (at < g->count &&
        keycmp(g->nodes[at].key, g->nodes[at].klen, key, klen) == 0) {
        value = 1;
        at++;
    }
    if (at < g->count &&
        is_prefix(key, klen, g->nodes[at].key, g->nodes[at].klen))
        kids = 1;
    return kids * 10 + value;
}

static int mem_kill(void *impl, const unsigned char *key, size_t klen)
{
    gg_mem *g = impl;
    size_t from = lower_bound(g, key, klen);
    size_t to = from;
    while (to < g->count &&
           is_prefix(key, klen, g->nodes[to].key, g->nodes[to].klen)) {
        free(g->nodes[to].key);
        free(g->nodes[to].val);
        to++;
    }
    memmove(g->nodes + from, g->nodes + to,
            (g->count - to) * sizeof(gg_node));
    g->count -= (to - from);
    return GG_OK;
}

size_t gg_prefix_successor(const unsigned char *key, size_t klen,
                           unsigned char *out)
{
    memcpy(out, key, klen);
    size_t n = klen;
    while (n > 0) {
        if (out[n - 1] != 0xFF) {
            out[n - 1]++;
            return n;
        }
        n--;
    }
    return 0;
}

static int mem_order(void *impl,
                     const unsigned char *prefix, size_t plen,
                     const unsigned char *sub, size_t sublen,
                     int dir, char *out, size_t cap, size_t *outlen)
{
    gg_mem *g = impl;
    unsigned char seek[512];
    size_t at;
    if (plen + sublen + 1 > sizeof(seek)) return GG_ERR;
    if (dir >= 0) {
        if (sublen == 0) {
            /* first subscript under the prefix: first key strictly below
             * no descendant, i.e. first key with the prefix and longer */
            at = lower_bound(g, prefix, plen);
            if (at < g->count &&
                g->nodes[at].klen == plen &&
                keycmp(g->nodes[at].key, plen, prefix, plen) == 0)
                at++;                     /* skip the parent's own node */
        } else {
            memcpy(seek, prefix, plen);
            memcpy(seek + plen, sub, sublen);
            size_t sn = gg_prefix_successor(seek, plen + sublen, seek);
            if (sn == 0) return GG_END;
            at = lower_bound(g, seek, sn);
        }
        if (at >= g->count ||
            !is_prefix(prefix, plen, g->nodes[at].key, g->nodes[at].klen) ||
            g->nodes[at].klen == plen)
            return GG_END;
    } else {
        if (sublen == 0) {
            /* last subscript under the prefix: the key just before the
             * prefix's successor range */
            size_t sn = gg_prefix_successor(prefix, plen, seek);
            at = sn ? lower_bound(g, seek, sn) : g->count;
        } else {
            memcpy(seek, prefix, plen);
            memcpy(seek + plen, sub, sublen);
            at = lower_bound(g, seek, plen + sublen);
        }
        if (at == 0) return GG_END;
        at--;
        if (!is_prefix(prefix, plen, g->nodes[at].key, g->nodes[at].klen) ||
            g->nodes[at].klen == plen)
            return GG_END;
    }
    /* the sibling's subscript is the first subscript past the prefix in
     * whichever key we landed on (a descendant decodes the same) */
    size_t used = gg_decode_one(g->nodes[at].key + plen,
                                g->nodes[at].klen - plen,
                                out, cap, outlen);
    return used ? GG_OK : GG_ERR;
}

static const gg_ops mem_ops = {
    mem_close, mem_set, mem_get, mem_data, mem_kill, mem_order
};

gg_store *gg_open_mem(void)
{
    gg_store *s = calloc(1, sizeof(gg_store));
    gg_mem *g = calloc(1, sizeof(gg_mem));
    if (!s || !g) { free(s); free(g); return 0; }
    s->ops = &mem_ops;
    s->impl = g;
    return s;
}
