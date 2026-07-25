#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# mchain.sh — compile one program through the MUMPS-hosted pipeline:
# gal -> fallback (to fixpoint) -> galpy, every stage executed by a
# compiler that is itself MUMPS routines.
#
# Usage: bin/mchain.sh <input.gal> <output.py>
#
# The routine bundles come from ./mumpsself's phase A ($BUILD/mumpsself/
# {gal,fallback,galpy}); run `./mumpsself --quick` once to create them.
# Intermediates are named after the input, so concurrent chains do not
# collide. Export galmatrix=^X before running to keep every object of the
# run for retrospective inspection (tools/yottadb/routines/galdump.m).
set -e
BUILD="${GAL_BUILD:-$(cd "$(dirname "$(readlink -f "$0")")/../.." && pwd)/gal3build}"
W="$BUILD/mumpsself"
source /usr/local/etc/ydb_env_set > /dev/null 2>&1

IN="$1"; OUT="$2"
if [ -z "$IN" ] || [ -z "$OUT" ]; then
    echo "usage: mchain.sh <input.gal> <output.py>"; exit 1
fi
for A in gal fallback galpy; do
    if [ ! -d "$W/$A" ]; then
        echo "mchain: $W/$A missing — run ./mumpsself --quick first"; exit 1
    fi
done

T="$W/chain_$(basename "$IN" | tr -c 'A-Za-z0-9' _)"

run() {  # run <artifact> <in> <out>
    local dir="$W/$1" out="$3"
    rm -f "$out"
    ( export ydb_routines="$dir $ydb_routines"
      timeout 1800 mumps -run CompilerProgram "$2" "$out" ) > "$out.log" 2>&1
    if [ ! -s "$out" ]; then
        echo "mchain: the $1 stage produced nothing"; tail -3 "$out.log"; exit 1
    fi
}

run gal "$IN" "$T.gal"
cp "$T.gal" "$T.fb"
for n in 0 1 2 3 4; do
    run fallback "$T.fb" "$T.fb$n"
    cmp -s "$T.fb" "$T.fb$n" && break
    cp "$T.fb$n" "$T.fb"
done
run galpy "$T.fb" "$OUT"
echo "mchain complete: $OUT"
