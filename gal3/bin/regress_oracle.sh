#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# regress_oracle.sh — small programs that each pin a fixed compiler bug.
# Each case compiles through the full python-hosted chain and must produce
# the expected output; a silent regression in a shared inference shows up
# here rather than three artifacts downstream.
set -e
HERE="$(dirname "$(readlink -f "$0")")"
cd "$HERE/.."
source ../galenv
W=/tmp/gal_regress
rm -rf "$W"; mkdir -p "$W"
FAIL=0
TOTAL=0

check() {  # check <name> <source> <expected-output>
    TOTAL=$((TOTAL+1))
    local name="$1" src="$2" want="$3"
    python ~/.gal3/gal.py "$src" "$W/$name.gal"      > /dev/null 2>&1
    python ~/.gal3/fallback.py "$W/$name.gal" "$W/$name.f0" > /dev/null 2>&1
    python ~/.gal3/fallback.py "$W/$name.f0" "$W/$name.f1"  > /dev/null 2>&1
    python ~/.gal3/fallback.py "$W/$name.f1" "$W/$name.f2"  > /dev/null 2>&1
    python ~/.gal3/galpy.py "$W/$name.f2" "$W/$name.py"     > /dev/null 2>&1
    local got
    got=$(env PYTHONPATH="$HOME/.gal3" python "$W/$name.py" 2>&1 | head -20)
    if [ "$got" = "$want" ]; then
        echo "ok  $name"
    else
        echo "FAIL $name: expected [$want] got [$got]"
        FAIL=$((FAIL+1))
    fi
}

# 2026-07-19: a dialect sharing a class's name took the class-name registry
# entry, so 'class set <name>' spliced its members into the dialect and they
# vanished from the atomic and every artifact — silently.
check dialect_name_clash examples/regress/dialect_name_clash.txt "extra"

# 2026-07-19: the dialect + compressed-syntaxes lowering. The python chain
# has always handled it; the case is here because a HOSTED compiler can
# diverge on it by whitespace alone (the lowering appends a bare newline per
# statement whose Fallback_Declaration is the empty string, which a host that
# reads "" as "absent" drops). This oracle proves the construct still lowers
# to a working program; ./mumpsself, ./jsself and ./javaself are what compare
# the hosted output byte for byte.
check dialect_syntaxes_lowering examples/regress/dialect_syntaxes_lowering.txt "lowered"

# 2026-10-12: emit (say without the newline), pow, ord and chr are new
# elements, and integer was declared in the dialect with no generator in any
# backend. This pins the python chain; the other targets were checked by hand
# when the elements were added.
check emit_pow_ord_chr examples/regress/emit_pow_ord_chr.txt $'abc\n65\nB\n1024\n3'

echo
if [ "$FAIL" = 0 ]; then
    echo "REGRESSION ORACLE PASSED: $TOTAL cases"
    exit 0
fi
echo "regress_oracle: $FAIL of $TOTAL failed"
exit 1
