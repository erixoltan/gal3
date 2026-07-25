/* test_gg.c — MUMPS-semantics tests for the node operations, phrased the
 * way a MUMPS programmer would check them: set/get/$data/$order/kill over
 * a small mixed tree. */
#include "gg.h"
#include "ggencode.h"
#include <stdio.h>
#include <string.h>

static int failures = 0;

static void check(int cond, const char *what)
{
    if (!cond) {
        printf("FAIL: %s\n", what);
        failures++;
    }
}

/* helpers: build encoded keys from C-string subscript lists */
static size_t enc(unsigned char *out, size_t cap, int n, const char **subs)
{
    size_t lens[8];
    for (int i = 0; i < n; i++) lens[i] = strlen(subs[i]);
    return gg_encode(subs, lens, n, out, cap);
}

static void set2(gg_store *g, const char *a, const char *b, const char *v)
{
    const char *s[2] = { a, b };
    unsigned char k[128];
    size_t kl = enc(k, sizeof(k), b ? 2 : 1, s);
    check(gg_set(g, k, kl, v, strlen(v)) == GG_OK, "set ok");
}

static int get2(gg_store *g, const char *a, const char *b,
                char *out, size_t cap)
{
    const char *s[2] = { a, b };
    unsigned char k[128];
    size_t kl = enc(k, sizeof(k), b ? 2 : 1, s);
    size_t vl = 0;
    int rc = gg_get(g, k, kl, out, cap - 1, &vl);
    if (rc == GG_OK) out[vl] = '\0';
    return rc;
}

static int data2(gg_store *g, const char *a, const char *b)
{
    const char *s[2] = { a, b };
    unsigned char k[128];
    size_t kl = enc(k, sizeof(k), b ? 2 : 1, s);
    return gg_data(g, k, kl);
}

/* $order over the second subscript of ^(a, from) */
static const char *order2(gg_store *g, const char *a, const char *from,
                          int dir, char *out, size_t cap)
{
    const char *s[1] = { a };
    unsigned char p[128], sb[128];
    size_t pl = enc(p, sizeof(p), 1, s);
    size_t sl = from ? gg_encode_one(from, strlen(from), sb, sizeof(sb)) : 0;
    size_t ol = 0;
    int rc = gg_order(g, p, pl, sb, sl, dir, out, cap - 1, &ol);
    if (rc != GG_OK) return NULL;
    out[ol] = '\0';
    return out;
}

/* deterministic LCG so runs reproduce */
static unsigned long long lcg_state = 42;
static unsigned lcg(unsigned n)
{
    lcg_state = lcg_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return (unsigned)((lcg_state >> 33) % n);
}

/* differential fuzz: the same random op stream against both backends
 * must agree on every result */
static void fuzz(gg_store *a, gg_store *b, int rounds)
{
    static const char *names[] = { "A", "B", "7", ".5", "-2", "z", "07" };
    for (int r = 0; r < rounds; r++) {
        const char *s1 = names[lcg(7)], *s2 = names[lcg(7)];
        const char *subs[2] = { s1, s2 };
        size_t lens[2] = { strlen(s1), strlen(s2) };
        int n = 1 + (int)lcg(2);
        unsigned char k[64];
        size_t kl = gg_encode(subs, lens, n, k, sizeof(k));
        unsigned op = lcg(5);
        if (op == 0) {
            char v[16];
            int vn = snprintf(v, sizeof(v), "v%u", lcg(1000));
            gg_set(a, k, kl, v, (size_t)vn);
            gg_set(b, k, kl, v, (size_t)vn);
        } else if (op == 1) {
            char va[64], vb[64];
            size_t la = 0, lb = 0;
            int ra = gg_get(a, k, kl, va, sizeof(va), &la);
            int rb = gg_get(b, k, kl, vb, sizeof(vb), &lb);
            check(ra == rb && (ra != GG_OK ||
                  (la == lb && memcmp(va, vb, la) == 0)), "fuzz get agrees");
        } else if (op == 2) {
            check(gg_data(a, k, kl) == gg_data(b, k, kl), "fuzz $data agrees");
        } else if (op == 3 && lcg(4) == 0) {
            gg_kill(a, k, kl);
            gg_kill(b, k, kl);
        } else {
            unsigned char p[64], sb[64];
            size_t pl = gg_encode(subs, lens, 1, p, sizeof(p));
            size_t sl = gg_encode_one(s2, strlen(s2), sb, sizeof(sb));
            char oa[64], ob[64];
            size_t na = 0, nb = 0;
            int dir = lcg(2) ? 1 : -1;
            int ra = gg_order(a, p, pl, sb, sl, dir, oa, sizeof(oa), &na);
            int rb = gg_order(b, p, pl, sb, sl, dir, ob, sizeof(ob), &nb);
            check(ra == rb && (ra != GG_OK ||
                  (na == nb && memcmp(oa, ob, na) == 0)), "fuzz $order agrees");
        }
    }
}

static void run_suite(gg_store *g)
{
    char buf[128];

    /* build: ^("Names") tree with mixed numeric/string subscripts, plus a
     * valueless intermediate node (descendants only) */
    set2(g, "Names", "10", "ten");
    set2(g, "Names", "2", "two");
    set2(g, "Names", "-1", "minus");
    set2(g, "Names", ".5", "half");
    set2(g, "Names", "Alice", "person");
    set2(g, "Names", "07", "string-oh-seven");   /* non-canonic => string */
    set2(g, "Other", NULL, "root-value");

    /* get */
    check(get2(g, "Names", "2", buf, sizeof(buf)) == GG_OK &&
          strcmp(buf, "two") == 0, "get ^(Names,2)");
    check(get2(g, "Names", "99", buf, sizeof(buf)) == GG_UNDEF,
          "get undefined node");

    /* $data */
    check(data2(g, "Names", "2") == 1, "$data leaf = 1");
    check(data2(g, "Names", NULL) == 10, "$data valueless parent = 10");
    check(data2(g, "Other", NULL) == 1, "$data root with value = 1");
    check(data2(g, "Nope", NULL) == 0, "$data missing = 0");
    set2(g, "Names", NULL, "now-with-value");
    check(data2(g, "Names", NULL) == 11, "$data value+kids = 11");

    /* $order forward walks canonic collation:
     * -1 < .5 < 2 < 10 < "07" < "Alice" */
    const char *expect[] = { "-1", ".5", "2", "10", "07", "Alice" };
    const char *cur = order2(g, "Names", NULL, 1, buf, sizeof(buf));
    int i = 0;
    while (cur && i < 6) {
        if (strcmp(cur, expect[i]) != 0) {
            printf("FAIL: $order step %d got '%s' want '%s'\n",
                   i, cur, expect[i]);
            failures++;
        }
        char prev[128];
        strcpy(prev, cur);
        cur = order2(g, "Names", prev, 1, buf, sizeof(buf));
        i++;
    }
    check(i == 6 && cur == NULL, "$order walks all six then ends");

    /* $order reverse from the end */
    cur = order2(g, "Names", NULL, -1, buf, sizeof(buf));
    check(cur && strcmp(cur, "Alice") == 0, "$order(-1) last is Alice");
    cur = order2(g, "Names", "Alice", -1, buf, sizeof(buf));
    check(cur && strcmp(cur, "07") == 0, "$order(-1) before Alice is 07");
    cur = order2(g, "Names", "-1", -1, buf, sizeof(buf));
    check(cur == NULL, "$order(-1) before first ends");

    /* $increment */
    {
        const char *s[1] = { "Counter" };
        unsigned char k[64];
        size_t kl = enc(k, sizeof(k), 1, s);
        long long r = 0;
        gg_increment(g, k, kl, 1, &r);
        check(r == 1, "$increment fresh = 1");
        gg_increment(g, k, kl, 5, &r);
        check(r == 6, "$increment adds");
        size_t vl = 0;
        gg_get(g, k, kl, buf, sizeof(buf) - 1, &vl);
        buf[vl] = '\0';
        check(strcmp(buf, "6") == 0, "$increment stores canonic value");
    }

    /* kill a subtree; siblings survive */
    {
        const char *s[1] = { "Names" };
        unsigned char k[64];
        size_t kl = enc(k, sizeof(k), 1, s);
        gg_kill(g, k, kl);
        check(data2(g, "Names", NULL) == 0, "kill removes subtree");
        check(data2(g, "Other", NULL) == 1, "kill spares siblings");
    }

}

int main(void)
{
    gg_store *m1 = gg_open_mem();
    run_suite(m1);
    gg_close(m1);

    const char *db = "/tmp/gg_test.lmdb";
    remove(db);
    remove("/tmp/gg_test.lmdb-lock");
    gg_store *l1 = gg_open_lmdb(db);
    check(l1 != NULL, "lmdb opens");
    if (l1) {
        run_suite(l1);
        /* persistence smoke: survive a close and reopen */
        const char *s[1] = { "Persist" };
        size_t ln[1] = { 7 };
        unsigned char k[32];
        size_t kl = gg_encode(s, ln, 1, k, sizeof(k));
        gg_set(l1, k, kl, "still here", 10);
        gg_close(l1);
        l1 = gg_open_lmdb(db);
        char v[32];
        size_t vl = 0;
        check(l1 && gg_get(l1, k, kl, v, sizeof(v), &vl) == GG_OK &&
              vl == 10 && memcmp(v, "still here", 10) == 0,
              "value survives close/reopen");
        gg_close(l1);
    }

    remove(db);
    remove("/tmp/gg_test.lmdb-lock");
    gg_store *fa = gg_open_mem();
    gg_store *fb = gg_open_lmdb(db);
    check(fb != NULL, "lmdb opens for fuzz");
    if (fb) {
        fuzz(fa, fb, 5000);
        gg_close(fb);
    }
    gg_close(fa);
    remove(db);
    remove("/tmp/gg_test.lmdb-lock");

    if (failures == 0) {
        printf("gg: all tests passed (mem + lmdb + differential fuzz)\n");
        return 0;
    }
    printf("gg: %d failures\n", failures);
    return 1;
}
