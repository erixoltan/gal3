/* gg_impl.h — the backend contract behind gg.h's public API. */
#ifndef GG_IMPL_H
#define GG_IMPL_H

#include "gg.h"

typedef struct gg_ops {
    void (*close)(void *impl);
    int (*set)(void *impl, const unsigned char *k, size_t kl,
               const char *v, size_t vl);
    int (*get)(void *impl, const unsigned char *k, size_t kl,
               char *out, size_t cap, size_t *vl);
    int (*data)(void *impl, const unsigned char *k, size_t kl);
    int (*kill)(void *impl, const unsigned char *k, size_t kl);
    int (*order)(void *impl, const unsigned char *p, size_t pl,
                 const unsigned char *s, size_t sl, int dir,
                 char *out, size_t cap, size_t *ol);
} gg_ops;

struct gg_store {
    const gg_ops *ops;
    void *impl;
};

/* shared helper: smallest key greater than every key prefixed by (key,klen);
 * returns 0 when none exists */
size_t gg_prefix_successor(const unsigned char *key, size_t klen,
                           unsigned char *out);

#endif
