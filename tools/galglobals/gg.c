/* gg.c — the public API dispatching to a backend, plus increment, which
 * is get+set on any backend. */
#include "gg_impl.h"
#include <stdio.h>
#include <stdlib.h>

void gg_close(gg_store *g)
{
    if (!g) return;
    g->ops->close(g->impl);
    free(g);
}

int gg_set(gg_store *g, const unsigned char *k, size_t kl,
           const char *v, size_t vl)
{ return g->ops->set(g->impl, k, kl, v, vl); }

int gg_get(gg_store *g, const unsigned char *k, size_t kl,
           char *out, size_t cap, size_t *vl)
{ return g->ops->get(g->impl, k, kl, out, cap, vl); }

int gg_data(gg_store *g, const unsigned char *k, size_t kl)
{ return g->ops->data(g->impl, k, kl); }

int gg_kill(gg_store *g, const unsigned char *k, size_t kl)
{ return g->ops->kill(g->impl, k, kl); }

int gg_order(gg_store *g,
             const unsigned char *p, size_t pl,
             const unsigned char *s, size_t sl,
             int dir, char *out, size_t cap, size_t *ol)
{ return g->ops->order(g->impl, p, pl, s, sl, dir, out, cap, ol); }

int gg_increment(gg_store *g, const unsigned char *k, size_t kl,
                 long long by, long long *result)
{
    char buf[32];
    size_t vl = 0;
    long long cur = 0;
    if (gg_get(g, k, kl, buf, sizeof(buf) - 1, &vl) == GG_OK) {
        buf[vl] = '\0';
        cur = strtoll(buf, NULL, 10);
    }
    cur += by;
    int n = snprintf(buf, sizeof(buf), "%lld", cur);
    if (n < 0) return GG_ERR;
    if (gg_set(g, k, kl, buf, (size_t)n) != GG_OK) return GG_ERR;
    *result = cur;
    return GG_OK;
}
