# gal3 Status

*Snapshot: 2026-07-20. What is done, in progress, and open. For how the pieces fit
together, see [architecture.md](architecture.md).*

## Headline

gal3 **self-hosts** and generates **six target languages** (Python, JavaScript,
Go, Java, C++, MUMPS), plus a frozen C proof of concept. It can also **parse
external Python** into gal elements and translate it back out. Fourteen
artifacts reach a byte-identical self-compilation fixpoint — and the compiler
itself now **runs in four languages**: Python, node (3.1), the JVM (3.2) and
YottaDB (3.3). Each hosted edition rebuilds the pipeline byte-identically.

## Done

### 3.3 — the compiler in MUMPS (2026-07-19)
- **The gal compiler runs on YottaDB.** `gal`, `fallback` and `galpy` each
  compile to a MUMPS routine bundle (one routine per class, flattened by
  the inheritance inference), so the whole `gal → fallback (to fixpoint) →
  galpy` pipeline executes inside MUMPS. On the five contract programs the
  MUMPS-hosted chain emits Python that is byte-identical to the
  Python-hosted chain's *and* runs identically. **It also rebuilds the
  compiler's own 150KB source at every stage** — `gal`, the full
  `fallback` fixpoint, and `galpy` — byte-identically. Gate:
  `./mumpsself`, green at 22 checks 2026-07-20 (`--quick` runs the five
  programs only, 20 checks, in a couple of minutes; the full run adds the
  compiler-source row and takes about an hour). Design and the eight
  python-vs-MUMPS semantic gaps that had to be closed:
  [mumps_design.md](mumps_design.md).
- Objects live in a matrix that is a *local* by default and a global when
  `galmatrix=^X` — so a compile can be inspected afterward, object by
  object, with `tools/yottadb/routines/galdump.m`. This retrospective
  database found several of the bugs above, including one it was designed
  for: seeing which class actually occupies a property.
- Collections are handles into that matrix, giving Python's reference
  semantics exactly; dictionaries iterate in insertion order; lists carry
  their own count (an O(n) `llength` had made the compiler O(n²)).
- **A latent pipeline bug, found because MUMPS links statically**: a
  `dialect` sharing a class's name took the class-name registry entry, so
  `class set <that name>` spliced its members into the dialect — where
  nothing emits them. `Compiler.Data_Type_Report` had been missing from
  the atomic and from *every* artifact, in silence, because its only
  caller is verbose-guarded. Fixed in the Attributes inference; pinned by
  `bin/regress_oracle.sh`.

### 3.1 — the compiler in JavaScript; no implicit Base (2026-07-16)
- `jsself` green for **all twelve artifacts** (`gal`, `fallback`, `galpy`,
  `galjs`, `pylex`, `pyparse`, `pygen`, `galgo`, `galjava`, `galcpp`,
  `galc`, `pygal`): the JS chain rebuilds each with byte-identical
  `.gal`/`.atomic`/`.py`/`.js` at every stage, including the JS fixpoint
  (JS-built-JS ≡ Python-built-JS). Mixed Python/node chains interoperate by
  construction. Dictionaries compile to `Map`; gal objects are wrapped by
  `Gal_New` proxies for Python-AttributeError parity; `debug;` throws under
  node. Design + findings: [js_selfhost_design.md](js_selfhost_design.md).
- The JS editions also *run*: `pylex.js`/`pyparse.js`/`pygen.js` reproduce
  their Python editions' output byte-for-byte on real input, and `pygal.js`
  translates the five-languages artifacts identically (matching failure
  modes on the known pygal gaps). The peg-generated Python parser's
  memoization machinery works under node unchanged.
- Base/constructor/super redesign: the fallback no longer appends ` is Base`
  to ancestor-less classes — standalone programs no longer need `class
  Base;`. New explicit `super A B;` statement (Python/JS; validated: inside a
  constructor, class has an ancestor, first statement); constructors without
  an explicit super pass nothing to the parent.
- `.elems` reports are written only on error paths.

### Self-hosting fixpoint — 3.0.0 (2026-06-10), 3.0.1 (2026-07-01)
- All fourteen artifacts (`gal`, `fallback`, `galpy`, `galjs`, `galgo`,
  `galjava`, `galcpp`, `galc`, `galmumps`, `peg`, `pylex`, `pyparse`, `pygen`,
  `pygal`) are byte-identical between `selfbuild` (`_3`) and `selfself`
  (`_33`). (`galmumps` joined the set for 3.3; the count was thirteen through
  3.1.)
- gal2 building gal3 vs. gal3 building gal3 produce the same compiler. gal2 is
  now purely a bootstrap step.
- Verified by the standard loop: `./build && ./selfbuild && py_compile && ./selfself`,
  then diffing `_3` vs `_33`.

### Six target languages
- **Python** (`galpy`) and **JavaScript** (`galjs`) — complete; both are
  self-hosting targets (`galjs` since 3.0.1). All four compiler atomics
  translate to node-clean JS.
- **Go** (`galgo`) — complete 2026-07-11. module → `package main`, class →
  struct + pointer-receiver methods, list/dict → slice/map.
- **Java** (`galjava`) — complete 2026-07-12. module → the public class holding
  `main`; gal classes → package-private siblings; `javac -Xlint:all -Werror`
  clean.
- **C++** (`galcpp`) — complete 2026-07-12. `std::`-qualified, objects on the
  stack, `g++ -std=c++17 -Wall -Wextra -Werror` clean. Replaced C as the
  native/manual-memory point on the language spectrum.
- **MUMPS** (`galmumps`) — complete 2026-07-19, and the third compiler host.
  module → one routine; each class → one routine of labels with inheritance
  flattened at compile time (the flattening *is* the vtable); objects and
  collections → nodes in a matrix that can be a local (transient) or a global
  (persistent, and inspectable after the run).
- Each backend is an `<lang>_inference.txt` + `<lang>_main.txt` pair mirroring
  `python_inference.txt`, wired into `build`/`selfbuild`/`selfself`.

### Data type inference (2026-07-06)
- Ported gal2 → gal3 (`data_type_inference.txt`, in the zero stack). Runs on
  every compile and is behavior-neutral (fixpoint holds).
- Drives typed-target code: `say` → `printf`/formatted output with the right
  conversions, and string-operand-in-numeric-context conversions
  (`int()`/`Number()`/`std::stoi`/`Integer.parseInt`/`strconv.Atoi`) — one
  inference, five type systems. See [data_type_inference.md](data_type_inference.md).

### Parsing external Python (2026-07-03 → 07-06)
The front half of the universal-translator vision. See
[peg_python_parsing_design.md](peg_python_parsing_design.md).
- **`peg`** — parses pegen grammar files; generates a gal parser from
  `grammars/python-3.11.gram`. Includes packrat memoization and Warth-style
  left-recursion (both live only in the gal3 generators).
- **`pylex`** — Python tokenizer; 50/52 stdlib modules byte-identical vs.
  CPython (the 2 failures are 3.12+ syntax correctly rejected by the 3.11 pin).
- **`pyparse`** — Python parser; **49/49** 3.11-compatible stdlib modules
  accepted, at the same acceptance boundary as CPython. Must be built by the
  gal3 chain (needs memoization + left-recursion).
- **`pygen`** — regenerates normalized, PEP 8-spaced Python from the parse tree;
  **49/49** stdlib on an ast-equality + idempotence oracle.
- **`pygal`** — translates parsed Python into the gal Python dialect, then
  `fallback` lowers those elements toward the gal compiler dialect. Round-trips
  gal-generated Python (incl. the compiler's own artifacts) byte-identically.

## In progress

### Five programs × six languages
Code and oracle are done; the article and validation are not.
- All five sample programs frozen in `gal3/examples/`: `example.txt` (hello),
  `fizzbuzz.txt`, `bank.txt`, `receipt.txt`, `checkout.txt`.
- The oracle `gal3/bin/five_oracle.sh` is **green at 31 cells** as of 2026-07-19
  — the 5×6 matrix (py, js, cpp, go, java, mumps) plus the frozen hello×c cell
  — every program's outputs byte-identical across targets. The article was
  scoped as five languages; MUMPS arrived later as a sixth column and is a
  choice for the writing, not a requirement.
- **Remaining:** finish broader testing/validation of the initiative, draft the
  article / book chapter from the oracle's artifacts, and record the five-video
  series. Plan and coverage contract: [five_languages.md](five_languages.md).

## Open / deferred

### C target
Frozen at a hello + main-only-scalars POC (`c_inference.txt`, `galc`). Full
gal→C means hand-building a string/collection/object runtime — a real project of
its own, deferred. The oracle keeps one `hello × c` cell as a beachhead. (The C
driver also still has a silent-per-element-error hole the newer drivers fixed —
fix when C is picked back up.)

### Python-parsing tail
Still open from the parsing initiative: with-open write idiom, `Value=` kwarg,
multi-guard `defined`, `sorted`/`open`/encoding args, non-classmethod
decorators, method return types at call sites (`Operation_Call` untyped —
needs a method registry), `[my A B]` attribute chains, typing of
`iterate`/`for each` loop vars, and megabyte-scale parse time.

### Java: a `[null]` argument becomes a null varargs array
Three call sites in `pygal.java` emit `galrt.call(T, "Gal3_Expr", null)`,
where Java reads the `null` as the whole varargs array rather than one
element — so `args.length` would NPE, and the arity would read as 0. Only
`pygal` is affected, and `javaself` verifies that row by compiling and
rebuilding it rather than running it, so the gate stays green and the path
is unexercised. Fix is one condition in the two call generators (emit
`(Object) null`) plus a null guard in `galrt.call`. Found 2026-07-20 in
javac's own warnings; details in
[java_selfhost_design.md](java_selfhost_design.md).

### nsl backend
`nsl_base.txt` / `nsl_main.txt` exist but are commented out of the build. The
line-oriented nsl surface syntax is dormant.

### Documentation
- `docs/language_ref/gal3_language_reference.md` predates self-hosting and uses
  some non-current examples (`writeline` rather than `say`). It was intentionally
  left untouched in this pass and is due for a refresh.
- Historical planning docs live in `docs/history/` — the original April-2025
  LLM-centric vision, kept as a record. They do **not** describe the compiler
  that was built.

## Next

Both hosts that were "next" in the 2026-07-16 snapshot have shipped: **3.2
(Java)** on 2026-07-18 and **3.3** on 2026-07-19 — as MUMPS rather than the
Go that was pencilled in, because the gal2 MUMPS work (compile-time
inheritance flattening, objects in a database) turned out to be the more
interesting question and the one that stressed the design hardest. Go remains
available as a host whenever the native-single-binary distribution story
matters; C# is still the cheap add beside Java.

Candidates, in no fixed order:

- **Package and release.** The original goal behind maturing gal3: `galpy` on
  PyPI and `galjs` on npm. Nothing blocks this technically now.
- **The five-languages article, book chapter, and videos** — the last
  unfinished piece of a completed initiative (see In progress, above).
- **Finish the Python-parsing tail** (below) toward round-tripping arbitrary
  Python.
- **Revive `galc` on the galglobals runtime.** Both prerequisites now exist:
  compile-time inheritance flattening (3.3) and a collections/persistence
  layer (`tools/galglobals`, LMDB-backed, tested against YottaDB's own
  collation). This is the path to gal→C without hand-writing an object
  runtime from nothing.
- **A `persistent` surface for MUMPS** — the retrospective database
  (`galmatrix=^X`) is already useful for compiler research; making
  persistence a declared language feature rather than an env var would make
  it useful to programs.
