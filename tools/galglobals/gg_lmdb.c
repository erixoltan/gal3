/* gg_lmdb.c — the persistent backend: the same node contract over an
 * LMDB B-tree. Keys are gg_encode tuples, so LMDB's default bytewise
 * key order is MUMPS collation, a parent is a byte-prefix of its
 * descendants, and every operation is a plain cursor pattern.
 * Correctness-first: one transaction per operation. */
#include "gg_impl.h"
#include "ggencode.h"
#include <lmdb.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    MDB_env *env;
    MDB_dbi dbi;
} gg_lmdb;

static void lm_close(void *impl)
{
    gg_lmdb *g = impl;
    if (!g) return;
    mdb_env_close(g->env);
    free(g);
}

static int lm_set(void *impl, const unsigned char *k, size_t kl,
                  const char *v, size_t vl)
{
    gg_lmdb *g = impl;
    MDB_txn *txn;
    if (mdb_txn_begin(g->env, NULL, 0, &txn)) return GG_ERR;
    MDB_val key = { kl, (void *)k }, val = { vl, (void *)v };
    int rc = mdb_put(txn, g->dbi, &key, &val, 0);
    if (rc) { mdb_txn_abort(txn); return GG_ERR; }
    return mdb_txn_commit(txn) ? GG_ERR : GG_OK;
}

static int lm_get(void *impl, const unsigned char *k, size_t kl,
                  char *out, size_t cap, size_t *vl)
{
    gg_lmdb *g = impl;
    MDB_txn *txn;
    if (mdb_txn_begin(g->env, NULL, MDB_RDONLY, &txn)) return GG_ERR;
    MDB_val key = { kl, (void *)k }, val;
    int rc = mdb_get(txn, g->dbi, &key, &val);
    if (rc == MDB_NOTFOUND) { mdb_txn_abort(txn); return GG_UNDEF; }
    if (rc || val.mv_size > cap) { mdb_txn_abort(txn); return GG_ERR; }
    memcpy(out, val.mv_data, val.mv_size);
    *vl = val.mv_size;
    mdb_txn_abort(txn);
    return GG_OK;
}

static int lm_data(void *impl, const unsigned char *k, size_t kl)
{
    gg_lmdb *g = impl;
    MDB_txn *txn;
    MDB_cursor *cur;
    int value = 0, kids = 0;
    if (mdb_txn_begin(g->env, NULL, MDB_RDONLY, &txn)) return GG_ERR;
    if (mdb_cursor_open(txn, g->dbi, &cur)) { mdb_txn_abort(txn); return GG_ERR; }
    MDB_val key = { kl, (void *)k }, val;
    int rc = mdb_cursor_get(cur, &key, &val, MDB_SET_RANGE);
    if (rc == 0 && key.mv_size == kl && memcmp(key.mv_data, k, kl) == 0) {
        value = 1;
        rc = mdb_cursor_get(cur, &key, &val, MDB_NEXT);
    }
    if (rc == 0 && key.mv_size > kl && memcmp(key.mv_data, k, kl) == 0)
        kids = 1;
    mdb_cursor_close(cur);
    mdb_txn_abort(txn);
    return kids * 10 + value;
}

static int lm_kill(void *impl, const unsigned char *k, size_t kl)
{
    gg_lmdb *g = impl;
    MDB_txn *txn;
    MDB_cursor *cur;
    if (mdb_txn_begin(g->env, NULL, 0, &txn)) return GG_ERR;
    if (mdb_cursor_open(txn, g->dbi, &cur)) { mdb_txn_abort(txn); return GG_ERR; }
    MDB_val key = { kl, (void *)k }, val;
    int rc = mdb_cursor_get(cur, &key, &val, MDB_SET_RANGE);
    while (rc == 0 && key.mv_size >= kl && memcmp(key.mv_data, k, kl) == 0) {
        if (mdb_cursor_del(cur, 0)) { rc = -1; break; }
        rc = mdb_cursor_get(cur, &key, &val, MDB_NEXT);
    }
    mdb_cursor_close(cur);
    if (rc != 0 && rc != MDB_NOTFOUND) { mdb_txn_abort(txn); return GG_ERR; }
    return mdb_txn_commit(txn) ? GG_ERR : GG_OK;
}

static int lm_order(void *impl,
                    const unsigned char *prefix, size_t plen,
                    const unsigned char *sub, size_t sublen,
                    int dir, char *out, size_t cap, size_t *ol)
{
    gg_lmdb *g = impl;
    unsigned char seek[512];
    MDB_txn *txn;
    MDB_cursor *cur;
    if (plen + sublen + 1 > sizeof(seek)) return GG_ERR;
    if (mdb_txn_begin(g->env, NULL, MDB_RDONLY, &txn)) return GG_ERR;
    if (mdb_cursor_open(txn, g->dbi, &cur)) { mdb_txn_abort(txn); return GG_ERR; }
    MDB_val key, val;
    int rc, found = 0;
    if (dir >= 0) {
        if (sublen == 0) {
            key.mv_size = plen;
            key.mv_data = (void *)prefix;
            rc = mdb_cursor_get(cur, &key, &val, MDB_SET_RANGE);
            if (rc == 0 && key.mv_size == plen &&
                memcmp(key.mv_data, prefix, plen) == 0)
                rc = mdb_cursor_get(cur, &key, &val, MDB_NEXT);
        } else {
            memcpy(seek, prefix, plen);
            memcpy(seek + plen, sub, sublen);
            size_t sn = gg_prefix_successor(seek, plen + sublen, seek);
            if (sn == 0) rc = MDB_NOTFOUND;
            else {
                key.mv_size = sn;
                key.mv_data = seek;
                rc = mdb_cursor_get(cur, &key, &val, MDB_SET_RANGE);
            }
        }
        if (rc == 0 && key.mv_size > plen &&
            memcmp(key.mv_data, prefix, plen) == 0)
            found = 1;
    } else {
        if (sublen == 0) {
            size_t sn = gg_prefix_successor(prefix, plen, seek);
            if (sn == 0) {
                rc = mdb_cursor_get(cur, &key, &val, MDB_LAST);
            } else {
                key.mv_size = sn;
                key.mv_data = seek;
                rc = mdb_cursor_get(cur, &key, &val, MDB_SET_RANGE);
                if (rc == 0)
                    rc = mdb_cursor_get(cur, &key, &val, MDB_PREV);
                else
                    rc = mdb_cursor_get(cur, &key, &val, MDB_LAST);
            }
        } else {
            memcpy(seek, prefix, plen);
            memcpy(seek + plen, sub, sublen);
            key.mv_size = plen + sublen;
            key.mv_data = seek;
            rc = mdb_cursor_get(cur, &key, &val, MDB_SET_RANGE);
            if (rc == 0)
                rc = mdb_cursor_get(cur, &key, &val, MDB_PREV);
            else
                rc = mdb_cursor_get(cur, &key, &val, MDB_LAST);
        }
        if (rc == 0 && key.mv_size > plen &&
            memcmp(key.mv_data, prefix, plen) == 0)
            found = 1;
    }
    int ret = GG_END;
    if (found) {
        size_t used = gg_decode_one((unsigned char *)key.mv_data + plen,
                                    key.mv_size - plen, out, cap, ol);
        ret = used ? GG_OK : GG_ERR;
    }
    mdb_cursor_close(cur);
    mdb_txn_abort(txn);
    return ret;
}

static const gg_ops lmdb_ops = {
    lm_close, lm_set, lm_get, lm_data, lm_kill, lm_order
};

gg_store *gg_open_lmdb(const char *path)
{
    gg_lmdb *g = calloc(1, sizeof(gg_lmdb));
    gg_store *s = calloc(1, sizeof(gg_store));
    if (!g || !s) { free(g); free(s); return NULL; }
    if (mdb_env_create(&g->env)) { free(g); free(s); return NULL; }
    mdb_env_set_mapsize(g->env, (size_t)1 << 30);
    if (mdb_env_open(g->env, path, MDB_NOSUBDIR, 0664)) {
        mdb_env_close(g->env);
        free(g);
        free(s);
        return NULL;
    }
    MDB_txn *txn;
    if (mdb_txn_begin(g->env, NULL, 0, &txn) ||
        mdb_dbi_open(txn, NULL, 0, &g->dbi) ||
        mdb_txn_commit(txn)) {
        mdb_env_close(g->env);
        free(g);
        free(s);
        return NULL;
    }
    s->ops = &lmdb_ops;
    s->impl = g;
    return s;
}
