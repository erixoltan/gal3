/* test_ydb_diff.c — ground truth: YottaDB's own subscript collation must
 * match the gg encoding's memcmp order. The fixture subscripts are set
 * as ^ggtest(sub) through the SimpleAPI, walked with
 * ydb_subscript_next_s, and the walk must visit them in exactly the
 * order the encoded keys sort. Run under a ydb environment
 * (ydb_env_set). */
#include "ggencode.h"
#include <libyottadb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *fixture[] = {
    "", "-1000000", "-999.5", "-100", "-7", "-1.5", "-1", "-.5", "-.05",
    "0", ".005", ".05", ".5", ".55", "1", "1.05", "1.5", "2", "7", "10",
    "100", "999.5", "123456789012345678",
    " leading space", "-0", "-01", ".50", "0.5", "007", "07",
    "A", "Abc", "Z", "a", "abc", "abd", "z", "~tilde",
};
#define N ((int)(sizeof(fixture) / sizeof(fixture[0])))

typedef struct {
    const char *s;
    unsigned char enc[64];
    size_t elen;
} row;

static int cmp_enc(const void *a, const void *b)
{
    const row *x = a, *y = b;
    size_t m = x->elen < y->elen ? x->elen : y->elen;
    int c = memcmp(x->enc, y->enc, m);
    if (c) return c;
    return x->elen < y->elen ? -1 : (x->elen > y->elen ? 1 : 0);
}

int main(void)
{
    ydb_buffer_t g, sub, val;
    char subbuf[128], valbuf[8] = "1";
    int failures = 0;

    YDB_LITERAL_TO_BUFFER("^ggtest", &g);
    sub.buf_addr = subbuf;
    sub.len_alloc = sizeof(subbuf);
    val.buf_addr = valbuf;
    val.len_used = 1;
    val.len_alloc = sizeof(valbuf);

    /* clean slate, then set every fixture subscript */
    if (ydb_delete_s(&g, 0, NULL, YDB_DEL_TREE) != YDB_OK) {
        printf("FAIL: ydb_delete_s (is the ydb environment set?)\n");
        return 1;
    }
    for (int i = 0; i < N; i++) {
        sub.len_used = (unsigned)strlen(fixture[i]);
        memcpy(subbuf, fixture[i], sub.len_used);
        /* the empty string cannot be a stored subscript in ydb by
         * default; it stands for "start of order" instead — skip it */
        if (sub.len_used == 0) continue;
        if (ydb_set_s(&g, 1, &sub, &val) != YDB_OK) {
            printf("FAIL: ydb_set_s '%s'\n", fixture[i]);
            failures++;
        }
    }

    /* sort the same fixture by the gg encoding (dropping "") */
    row rows[64];
    int nr = 0;
    for (int i = 0; i < N; i++) {
        if (fixture[i][0] == '\0') continue;
        rows[nr].s = fixture[i];
        rows[nr].elen = gg_encode_one(fixture[i], strlen(fixture[i]),
                                      rows[nr].enc, sizeof(rows[nr].enc));
        nr++;
    }
    qsort(rows, (size_t)nr, sizeof(row), cmp_enc);

    /* walk ydb's $order from "" and compare step by step */
    sub.len_used = 0;
    for (int i = 0; i < nr; i++) {
        int rc = ydb_subscript_next_s(&g, 1, &sub, &sub);
        if (rc != YDB_OK) {
            printf("FAIL: ydb walk ended early at step %d\n", i);
            failures++;
            break;
        }
        if (sub.len_used != strlen(rows[i].s) ||
            memcmp(sub.buf_addr, rows[i].s, sub.len_used) != 0) {
            printf("FAIL: step %d ydb='%.*s' gg='%s'\n",
                   i, (int)sub.len_used, sub.buf_addr, rows[i].s);
            failures++;
        }
    }
    if (ydb_subscript_next_s(&g, 1, &sub, &sub) != YDB_ERR_NODEEND) {
        printf("FAIL: ydb walk has extra entries\n");
        failures++;
    }

    ydb_delete_s(&g, 0, NULL, YDB_DEL_TREE);
    if (failures == 0) {
        printf("ydb-diff: yottadb collation == gg encoding order (%d subscripts)\n", nr);
        return 0;
    }
    printf("ydb-diff: %d failures\n", failures);
    return 1;
}
