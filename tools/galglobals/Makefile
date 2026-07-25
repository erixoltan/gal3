CFLAGS=-Wall -Wextra -Werror -O2

test: test_ggencode test_gg
	./test_ggencode
	./test_gg

test_ggencode: test_ggencode.c ggencode.c ggencode.h
	cc $(CFLAGS) -o test_ggencode test_ggencode.c ggencode.c

test_gg: test_gg.c gg.c gg_mem.c gg_lmdb.c ggencode.c gg.h gg_impl.h ggencode.h
	cc $(CFLAGS) -o test_gg test_gg.c gg.c gg_mem.c gg_lmdb.c ggencode.c -llmdb

# ground truth vs yottadb: needs a ydb environment (source ydb_env_set)
test_ydb_diff: test_ydb_diff.c ggencode.c ggencode.h
	cc $(CFLAGS) $(shell pkg-config --cflags yottadb) -o test_ydb_diff test_ydb_diff.c ggencode.c $(shell pkg-config --libs yottadb)

ydbtest: test_ydb_diff
	bash -c 'source /usr/local/etc/ydb_env_set > /dev/null 2>&1; ./test_ydb_diff'

clean:
	rm -f test_ggencode test_gg test_ydb_diff
