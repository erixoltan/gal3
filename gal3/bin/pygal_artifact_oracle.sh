#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# pygal artifact oracle: translate a gal3-generated python artifact back to
# gal3, recompile it through the chain, and verify the recompiled program
# behaves byte-identically to the original on real inputs.
#
# Usage: pygal_artifact_oracle.sh <artifact.py> <test-input> [test-input ...]
# The artifact must take <input> <output> arguments (pylex-style).
# Work files land in /tmp/pygal_artifact/<name>/ for inspection.

set -e
HERE="$(dirname "$(readlink -f "$0")")"
cd "$HERE/.."
source ../galenv

ART="$1"; shift
NAME=$(basename "$ART" .py)
W=/tmp/pygal_artifact/$NAME
mkdir -p "$W"

echo "=== translate $NAME ==="
timeout 3600 python ~/.gal3/pygal.py "$ART" "$W/prog.gal3" 2>&1 | tail -1
[ -f "$W/prog.gal3" ] || { echo "TRANSLATION FAILED"; exit 1; }

echo "=== recompile through the gal3 chain ==="
rm -f "$W"/prog_t.*
python ~/.gal3/gal.py "$W/prog.gal3" "$W/prog_t.gal" > /dev/null 2>&1 || true
[ -f "$W/prog_t.gal" ] || { echo "GAL STAGE FAILED"; exit 1; }
P="$W/prog_t.gal"
for i in 0 1 2 3 4 5; do
    python ~/.gal3/fallback.py "$P" "$W/prog_t.fb$i" > /dev/null 2>&1 || true
    [ -f "$W/prog_t.fb$i" ] || { echo "FALLBACK $i FAILED"; exit 1; }
    if cmp -s "$P" "$W/prog_t.fb$i"; then break; fi
    P="$W/prog_t.fb$i"
done
python ~/.gal3/galpy.py "$P" "$W/prog_t.py" > /dev/null 2>&1 || true
[ -f "$W/prog_t.py" ] || { echo "GALPY STAGE FAILED"; exit 1; }

echo "=== behavioral comparison ==="
FAIL=0
for f in "$@"; do
    rm -f "$W/o.out" "$W/t.out"
    PYTHONPATH=$HOME/.gal3 timeout 600 python "$ART" "$f" "$W/o.out" > /dev/null 2>&1 || true
    PYTHONPATH=$HOME/.gal3 timeout 600 python "$W/prog_t.py" "$f" "$W/t.out" > /dev/null 2>&1 || true
    if [ -f "$W/o.out" ] && [ -f "$W/t.out" ] && cmp -s "$W/o.out" "$W/t.out"; then
        echo "  IDENTICAL: $(basename $f) ($(wc -c < "$W/o.out") bytes)"
    else
        echo "  DIFFER/FAILED: $f"
        FAIL=1
    fi
done
[ $FAIL -eq 0 ] && echo "ORACLE PASSED: $NAME" || { echo "ORACLE FAILED: $NAME"; exit 1; }
