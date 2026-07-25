/* test_ggencode.c — the encoding must reproduce MUMPS canonic collation
 * under memcmp, round-trip every subscript, and keep tuples prefix-free. */
#include "ggencode.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures = 0;

static void check(int cond, const char *what)
{
    if (!cond) {
        printf("FAIL: %s\n", what);
        failures++;
    }
}

/* the canonical ordering fixture: strictly ascending in MUMPS collation */
static const char *ordered[] = {
    "",            /* empty first */
    "-1000000", "-999.5", "-100", "-7", "-1.5", "-1", "-.5", "-.05",
    "0",
    ".005", ".05", ".5", ".55", "1", "1.05", "1.5", "2", "7", "10",
    "100", "999.5", "123456789012345678",
    /* strings, byte order; non-canonic numerics are strings */
    " leading space", "-0", "-01", ".50", "0.5", "007", "07",
    "A", "Abc", "Z", "a", "abc", "abd", "z", "~tilde",
};

static void test_ordering(void)
{
    int n = (int)(sizeof(ordered) / sizeof(ordered[0]));
    unsigned char enc[64][64];
    size_t elen[64];
    for (int i = 0; i < n; i++) {
        elen[i] = gg_encode_one(ordered[i], strlen(ordered[i]), enc[i], 64);
        check(elen[i] > 0, "encode succeeds");
    }
    for (int i = 0; i + 1 < n; i++) {
        size_t m = elen[i] < elen[i + 1] ? elen[i] : elen[i + 1];
        int c = memcmp(enc[i], enc[i + 1], m);
        if (c == 0) c = (elen[i] < elen[i + 1]) ? -1 : 1;
        if (c >= 0) {
            printf("FAIL: order '%s' !< '%s'\n", ordered[i], ordered[i + 1]);
            failures++;
        }
    }
}

static void test_roundtrip(void)
{
    int n = (int)(sizeof(ordered) / sizeof(ordered[0]));
    for (int i = 0; i < n; i++) {
        unsigned char enc[64];
        char back[64];
        size_t sublen = 0;
        size_t e = gg_encode_one(ordered[i], strlen(ordered[i]), enc, 64);
        size_t used = gg_decode_one(enc, e, back, 64, &sublen);
        if (used != e || sublen != strlen(ordered[i]) ||
            memcmp(back, ordered[i], sublen) != 0) {
            printf("FAIL: roundtrip '%s' -> '%.*s'\n",
                   ordered[i], (int)sublen, back);
            failures++;
        }
    }
    /* embedded NUL in a string subscript */
    const char nul[] = { 'a', 0, 'b' };
    unsigned char enc[16];
    char back[16];
    size_t sublen = 0;
    size_t e = gg_encode_one(nul, 3, enc, 16);
    size_t used = gg_decode_one(enc, e, back, 16, &sublen);
    check(used == e && sublen == 3 && memcmp(back, nul, 3) == 0,
          "roundtrip embedded NUL");
}

static void test_canonic(void)
{
    check(gg_is_canonic("0", 1), "0 canonic");
    check(gg_is_canonic("7", 1), "7 canonic");
    check(gg_is_canonic("-1.5", 4), "-1.5 canonic");
    check(gg_is_canonic(".5", 2), ".5 canonic");
    check(gg_is_canonic("-.5", 3), "-.5 canonic");
    check(gg_is_canonic("10", 2), "10 canonic");
    check(!gg_is_canonic("", 0), "empty not canonic");
    check(!gg_is_canonic("-0", 2), "-0 not canonic");
    check(!gg_is_canonic("07", 2), "07 not canonic");
    check(!gg_is_canonic("0.5", 3), "0.5 not canonic");
    check(!gg_is_canonic("1.50", 4), "1.50 not canonic");
    check(!gg_is_canonic("1.", 2), "trailing dot not canonic");
    check(!gg_is_canonic(".", 1), "lone dot not canonic");
    check(!gg_is_canonic("1a", 2), "1a not canonic");
}

static void test_tuples(void)
{
    /* ("A",1) < ("A",1,"x") : parent is a strict prefix of its child */
    const char *t1[] = { "A", "1" };
    const char *t2[] = { "A", "1", "x" };
    size_t l1[] = { 1, 1 };
    size_t l2[] = { 1, 1, 1 };
    unsigned char e1[64], e2[64];
    size_t n1 = gg_encode(t1, l1, 2, e1, 64);
    size_t n2 = gg_encode(t2, l2, 3, e2, 64);
    check(n1 > 0 && n2 > n1, "tuple encode");
    check(memcmp(e1, e2, n1) == 0, "parent tuple is a prefix of child");
    /* ("A",2) sorts after every ("A",1,...) descendant */
    const char *t3[] = { "A", "2" };
    unsigned char e3[64];
    size_t n3 = gg_encode(t3, l1, 2, e3, 64);
    size_t m = n2 < n3 ? n2 : n3;
    check(memcmp(e2, e3, m) < 0, "sibling after descendants");
}

int main(void)
{
    test_canonic();
    test_ordering();
    test_roundtrip();
    test_tuples();
    if (failures == 0) {
        printf("ggencode: all tests passed\n");
        return 0;
    }
    printf("ggencode: %d failures\n", failures);
    return 1;
}
