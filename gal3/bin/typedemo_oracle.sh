#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# The data type demo oracle: compile examples/typedemo.txt to Python,
# JavaScript and C, run all three, and require byte-identical output.
# The three targets need type work to different extents - Python raises
# a TypeError without int(), JavaScript silently concatenates without
# Number(), and C needs typed declarations, printf formats and atoi -
# and every one of those decisions reads the inferred Data_Type and
# Usage properties.

set -e
HERE="$(dirname "$(readlink -f "$0")")"
cd "$HERE/.."
source ../galenv

W=/tmp/typedemo
mkdir -p "$W"
rm -f "$W"/t.* "$W"/out_* "$W"/t_c

python ~/.gal3/gal.py examples/typedemo.txt "$W/t.gal" > /dev/null 2>&1
python ~/.gal3/fallback.py "$W/t.gal" "$W/t.fb0" > /dev/null 2>&1
python ~/.gal3/fallback.py "$W/t.fb0" "$W/t.fb1" > /dev/null 2>&1
python ~/.gal3/galpy.py "$W/t.fb1" "$W/t.py" > /dev/null 2>&1
python ~/.gal3/galjs.py "$W/t.fb1" "$W/t.js" > /dev/null 2>&1
python ~/.gal3/galc.py "$W/t.fb1" "$W/t.c" > /dev/null 2>&1
for f in t.py t.js t.c; do
    [ -f "$W/$f" ] || { echo "FAILED to generate $f"; exit 1; }
done

gcc -o "$W/t_c" "$W/t.c"
PYTHONPATH=$HOME/.gal3 python "$W/t.py" > "$W/out_py.txt"
node "$W/t.js" > "$W/out_js.txt"
"$W/t_c" > "$W/out_c.txt"

if diff -q "$W/out_py.txt" "$W/out_js.txt" > /dev/null && diff -q "$W/out_py.txt" "$W/out_c.txt" > /dev/null; then
    echo "TYPEDEMO ORACLE PASSED: python, javascript and c outputs byte-identical"
    echo "conversion sites:"
    grep -n "int(Digits)" "$W/t.py"
    grep -n "Number(Digits)" "$W/t.js"
    grep -n "atoi(Digits)" "$W/t.c"
else
    echo "TYPEDEMO ORACLE FAILED: outputs differ"
    diff "$W/out_py.txt" "$W/out_c.txt" | head -5
    diff "$W/out_py.txt" "$W/out_js.txt" | head -5
    exit 1
fi
