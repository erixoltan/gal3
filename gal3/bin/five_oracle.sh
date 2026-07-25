#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# The five-languages oracle: compile the five article programs (hello,
# fizzbuzz, bank, receipt, checkout) to every implemented target and
# require byte-identical output per program across all its targets.
# This grows toward the 5x5 matrix of docs/five_languages.md: the CELLS
# table below whitelists the implemented cells, and a whitelisted cell
# that breaks fails the oracle loudly. checkout reads stdin, so fixed
# input is piped to every target: prompts count as output too.

set -e
HERE="$(dirname "$(readlink -f "$0")")"
cd "$HERE/.."
source ../galenv

# GAL_ORACLE_LANGS (optional): comma-separated whitelist to restrict which
# targets run, e.g. GAL_ORACLE_LANGS=py,js for the fast PR gate (no g++, go,
# javac or YottaDB needed). Unset = the full implemented matrix below.

# program:languages[:stdin]
CELLS="
hello:py,js,cpp,go,java,c,mumps
fizzbuzz:py,js,cpp,go,java,mumps
bank:py,js,cpp,go,java,mumps
receipt:py,js,cpp,go,java,mumps
checkout:py,js,cpp,go,java,mumps:3|5
"
declare -A SOURCE=( [hello]=examples/example.txt
                    [fizzbuzz]=examples/fizzbuzz.txt
                    [bank]=examples/bank.txt
                    [receipt]=examples/receipt.txt
                    [checkout]=examples/checkout.txt )

W=/tmp/five_oracle
rm -rf "$W"
mkdir -p "$W"
FAIL=0
TOTAL=0

for CELL in $CELLS; do
    PROG="${CELL%%:*}"
    REST="${CELL#*:}"
    LANGS="${REST%%:*}"
    STDIN=""
    [ "$REST" != "$LANGS" ] && STDIN="${REST#*:}"

    # Restrict to the whitelisted targets, if GAL_ORACLE_LANGS is set.
    if [ -n "$GAL_ORACLE_LANGS" ]; then
        KEEP=""
        for L in ${LANGS//,/ }; do
            case ",$GAL_ORACLE_LANGS," in *",$L,"*) KEEP="${KEEP:+$KEEP,}$L";; esac
        done
        LANGS="$KEEP"
    fi
    [ -z "$LANGS" ] && continue

    SRC="${SOURCE[$PROG]}"
    D="$W/$PROG"
    mkdir -p "$D"

    python ~/.gal3/gal.py "$SRC" "$D/t.gal"      > /dev/null 2>&1
    python ~/.gal3/fallback.py "$D/t.gal" "$D/t.fb0" > /dev/null 2>&1
    python ~/.gal3/fallback.py "$D/t.fb0" "$D/t.fb1" > /dev/null 2>&1

    for LANG in ${LANGS//,/ }; do
        TOTAL=$((TOTAL+1))
        case "$LANG" in
            py)
                python ~/.gal3/galpy.py "$D/t.fb1" "$D/t.py" > /dev/null 2>&1
                RUN=(env PYTHONPATH="$HOME/.gal3" python "$D/t.py") ;;
            js)
                python ~/.gal3/galjs.py "$D/t.fb1" "$D/t.js" > /dev/null 2>&1
                RUN=(node "$D/t.js") ;;
            c)
                python ~/.gal3/galc.py "$D/t.fb1" "$D/t.c" > /dev/null 2>&1
                gcc -o "$D/t_c" "$D/t.c"
                RUN=("$D/t_c") ;;
            cpp)
                python ~/.gal3/galcpp.py "$D/t.fb1" "$D/t.cpp" > /dev/null 2>&1
                g++ -std=c++17 -Wall -Wextra -Werror -o "$D/t_cpp" "$D/t.cpp"
                RUN=("$D/t_cpp") ;;
            go)
                python ~/.gal3/galgo.py "$D/t.fb1" "$D/t.go" > /dev/null 2>&1
                gofmt -w "$D/t.go"
                RUN=(go run "$D/t.go") ;;
            java)
                # java insists the file carry the public class's name,
                # which is the gal module's name: the program capitalized
                CLS="${PROG^}"
                python ~/.gal3/galjava.py "$D/t.fb1" "$D/$CLS.java" > /dev/null 2>&1
                javac -Xlint:all -Werror -d "$D" "$D/$CLS.java"
                RUN=(java -cp "$D" "$CLS") ;;
            mumps)
                # galmumps emits a routine bundle (;;;ROUTINE markers, one
                # section per class plus the module); split it into .m
                # files, add the minimal runtime, and run the module
                # routine under a ydb environment with the cell dir first
                CLS="${PROG^}"
                python ~/.gal3/galmumps.py "$D/t.fb1" "$D/bundle.m" > /dev/null 2>&1
                awk -v dir="$D" '/^;;;ROUTINE /{f=dir"/"$2".m"; next} f{print > f}' "$D/bundle.m"
                cp "$(dirname "$0")/galrt.m" "$D/"
                RUN=(bash -c "source /usr/local/etc/ydb_env_set > /dev/null 2>&1; export ydb_routines=\"$D \$ydb_routines\"; exec mumps -run $CLS") ;;
        esac
        if [ -n "$STDIN" ]; then
            echo "${STDIN//|/$'\n'}" | "${RUN[@]}" > "$D/out_$LANG.txt" \
                || { echo "FAIL $PROG/$LANG: runtime error"; FAIL=1; continue; }
        else
            "${RUN[@]}" > "$D/out_$LANG.txt" \
                || { echo "FAIL $PROG/$LANG: runtime error"; FAIL=1; continue; }
        fi
    done

    FIRST=""
    for OUT in "$D"/out_*.txt; do
        if [ -z "$FIRST" ]; then
            FIRST="$OUT"
        elif ! diff -q "$FIRST" "$OUT" > /dev/null; then
            echo "FAIL $PROG: $(basename "$FIRST") and $(basename "$OUT") differ"
            diff "$FIRST" "$OUT" | head -5
            FAIL=1
        fi
    done
    [ $FAIL -eq 0 ] && echo "ok  $PROG (${LANGS})"
done

if [ $FAIL -eq 0 ]; then
    echo "FIVE-LANGUAGES ORACLE PASSED: $TOTAL cells, outputs byte-identical per program"
else
    echo "FIVE-LANGUAGES ORACLE FAILED"
    exit 1
fi
