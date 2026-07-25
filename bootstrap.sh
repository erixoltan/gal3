#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
#
# bootstrap.sh — reproduce the gal3 compiler from the checked-in frozen
# stage-0 and prove the fixpoint, with no gal2 anywhere in the picture.
#
# This is the Go-toolchain pattern: a small, frozen build of the compiler
# (bootstrap/) is enough to compile the current sources into a fresh
# compiler (selfbuild), which then compiles the sources again (selfself).
# If the two generations are byte-identical, the compiler is a fixpoint of
# itself — it reproduces itself exactly. That equality is the whole proof.
#
# Prerequisites: only `uv` (https://astral.sh/uv). galenv fetches the
# pinned Python and dependencies into a local venv; nothing else is needed.
#
# Usage:  ./bootstrap.sh
# Result: "FIXPOINT OK" on success; non-zero exit and a FAIL line otherwise.
set -e

HERE="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"   # repo root
source "$HERE/galenv"

BIN="$HOME/.gal3"        # install/cache dir the self-build scripts read & write
mkdir -p "$BIN"

echo "seeding stage-0 compiler from bootstrap/ into $BIN"
cp "$HERE/bootstrap/gal.py"      "$BIN/gal.py"
cp "$HERE/bootstrap/fallback.py" "$BIN/fallback.py"
cp "$HERE/bootstrap/galpy.py"    "$BIN/galpy.py"
cp "$HERE/bootstrap/Runtime.py"  "$BIN/Runtime.py"

cd "$HERE/gal3"

echo
echo "=== selfbuild: stage-0 compiler builds the compiler (-> _3) ==="
./selfbuild

echo
echo "=== selfself: that compiler builds the compiler again (-> _33) ==="
./selfself

echo
echo "=== fixpoint: diff _3 vs _33 across all artifacts ==="
ARTIFACTS="gal fallback galpy galc galcpp galgo galjava galjs galmumps peg pylex pyparse pygen pygal"
fail=0
n=0
for a in $ARTIFACTS; do
    n=$((n+1))
    if cmp -s "$BIN/${a}_3.py" "$BIN/${a}_33.py"; then
        echo "  ok   $a"
    else
        echo "  FAIL $a  (_3 != _33)"
        fail=1
    fi
done

if [ "$fail" != 0 ]; then
    echo
    echo "FIXPOINT FAILED"
    exit 1
fi

# Install the freshly self-built, fixpoint-verified compiler as the active
# toolchain: promote every _3 artifact to its bare name in $BIN. This is what
# replaces the old gal2 seeding — downstream tools (the oracles, ./jsself,
# ./javaself, ./mumpsself) all read these bare names.
echo
echo "=== install: promoting self-built _3 artifacts to active names in $BIN ==="
for a in $ARTIFACTS; do
    cp "$BIN/${a}_3.py" "$BIN/${a}.py"
done

echo
echo "FIXPOINT OK — $n artifacts byte-identical across two self-hosted generations."
exit 0
