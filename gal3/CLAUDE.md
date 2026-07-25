# gal3 compiler — working guide

The `gal` programming language, version 3 (`gal` is always lowercase; it stands
for *general abstract language*). The `.txt` source files here are gal source —
they use `.txt` only to stop editors from syntax-highlighting them.

**gal3 self-hosts.** As of the 3.0.0 fixpoint (2026-06-10) and 3.0.1 (galjs,
2026-07-01), gal2 building gal3 and gal3 building gal3 produce byte-identical
compilers. gal2 (`~/.goalspell/goalspell`) is now only the bootstrap step.
Backends exist for **Python, JavaScript, Go, Java, C++, MUMPS** (all complete)
and **C** (frozen hello + main-only-scalars POC). The compiler itself also
*runs* under node (3.1), on the JVM (3.2) and on YottaDB (3.3). The
`peg`/`pylex`/`pyparse`/`pygen`/`pygal` toolchain parses external Python into
gal elements and back.

For the full picture read `../docs/architecture.md` and `../docs/status.md`.

## Build & fixpoint loop

```bash
./build && ./selfbuild && python -m py_compile ~/.gal3/*_3.py && ./selfself
# then diff _3 vs _33 for each artifact — must be empty:
for a in gal fallback galpy galjs galgo galjava galcpp galc galmumps peg pylex pyparse pygen pygal; do
    diff ~/.gal3/${a}_3.py ~/.gal3/${a}_33.py && echo "$a ok"
done
```

- `./build` = gal2 compiles `.txt` sources → `~/.gal3/{artifact}.py`.
- `./selfbuild` = those gal3 binaries recompile → `_3.py`.
- `./selfself` = `_3` binaries rebuild → `_33.py`. Done when `_3 ≡ _33`.
- Build artifacts land in `~/code/gal3build/`; run `python ~/.gal3/<artifact>.py
  <in> <out>`.
- Fast per-artifact rebuilds: `./pybuild`, `./pegbuild`, `./pyparsebuild`,
  `./pygenbuild`, `./pygalbuild`, `./galjavabuild`, `./galmumpsbuild`.
- Hosted-compiler gates: `./jsself` (node), `./javaself` (JVM),
  `./mumpsself` (YottaDB; `--quick` skips the compiler-source row). Each
  rebuilds the pipeline with the hosted edition and demands byte-identical
  output at every stage.

**The fixpoint diff is structural, not behavioral** — two consistently-wrong
generations diff clean. Always also run the relevant oracle in `bin/` (they
compare real program output to ground truth). `bin/five_oracle.sh` is the
5-programs × 6-languages check (python, js, c++, go, java, mumps);
`bin/regress_oracle.sh` runs the small programs that each pin a fixed
compiler bug — add a case there whenever you fix one.

## The pipeline (know which stage a bug is in)

`gal → fallback (repeat to fixpoint) → atomic → target`. A high-level element is
*lowered* through fallback into atomic gal, then a per-language generator emits
the target. When adding an abstraction, write its **fallback lowering** in gal —
backends only ever see the atomic result. See architecture.md for the full
inference list and the element-order contract (bottom-up inferences walk the flat
list forward, top-down walk it in reverse).

## Where to fix things (bootstrap discipline)

- The code you write today is compiled by **gal2**. If compiling a gal3
  definition of some statement goes wrong, and gal2 is the one miscompiling it,
  fix the **gal2** version, not the gal3 definition.
- Backends live in `<lang>_inference.txt` + `<lang>_main.txt`, each a 1:1 mirror
  of `python_inference.txt` (same generate list, language-specific bodies). To
  add a target, copy that structure and wire it into `build`/`selfbuild`/
  `selfself`.
- gal2 reference generators to port from: `../gal2/src/Python.gal`,
  `Fallback.gal` (proven, written in gal1 syntax).

## Debugging

Debug in the **target language**. Run generated Python under `zdebug`
(`~/.gal3/zdebug.py`), or `import` a compiled artifact as a module and introspect
its element tree directly (the real debug loop). `debug;` lowers to
`zdebug.zbreak()`.

- To see an error masked by a `debug;` in an unattended build: temporarily stub
  `~/.gal3/zdebug.py` with a no-op `zbreak`, then **restore it** so real `debug;`
  fires loudly again.
- On a parse failure, the high-water token (`Parser.High_Water`) points at the
  stall; map its char position back to a source line.
- **Under MUMPS, debug retrospectively.** Run with `galmatrix=^X` and every
  object the compile created survives the run; then inspect them with
  `tools/yottadb/routines/galdump.m` — `census`, `parser`, `find <Class>`,
  `node <n>`, `wipe` (wipe first, or a previous run pollutes the census).
  This answers questions no stack trace can: which class actually occupies
  an `object` property, what a classification really holds. `galprof.m`
  profiles a run line by line (`VIEW TRACE`). `debug;` enters `^%debug`
  (`~/.yottadb/r/_debug.m`) — never leave a stub `_debug.m` in the routine
  path, it shadows the real debugger.

## gal facts that cost hours (keep these in mind)

- **gal strings do not process escapes**: `'\n'` is two characters. Real control
  characters come from the literal syntaxes `[line]`, `[tab]`, `[return]` — and
  every backend's `Syntax_Line`/`Tab`/`Indent` generator must set
  `my Unquoted = [line]` (etc.) as a side effect, or comment/format builders emit
  the literal text `[line]`.
- **f-string / append double-escape family**: escape *per literal segment* at
  append time, then choose quotes — never run one escaper over an assembled body
  (it re-escapes embedded expression code). Nested appends must **flatten** at
  generation (nested same-quote f-strings are a pre-3.12 SyntaxError).
- **String-into-numeric conversion is driven by data type**: only a definite
  `string` data-type operand in a numeric op converts (`int()`/`Number()`/
  `std::stoi`/`Integer.parseInt`/`strconv.Atoi`); `variant`/unknown is left
  alone, so existing programs are unaffected and the fixpoint holds.
- **Precedence/associativity read the classification, not the parse element**:
  dereference `[Arg.Classification]` for precedence; a right operand
  parenthesizes at *equal* precedence. Class-`set` property defaults on
  generated-only classes are silently dropped — put precedence values in the
  dialect declaration itself (declaration properties do materialize in
  `__init__`).
- **Every ancestor-less class implicitly extends `Base`** (a universal arg-sink
  constructor). A standalone program with classes must declare `class Base;`
  itself.
- `push` is the list-append statement (not `list append`). Method params live in
  `Listargs` (not `Arguments`, which includes the type keyword + name). A
  statement classification's `.Parent` is the enclosing scoped statement; use
  `[P.Block Statements]` for siblings.
- **Name references resolve types via `Get_Variable_Context().Variables`**, not
  shared classification objects — classifications are per-token. Register a new
  scoped variable (e.g. a loop var) there.
- **Class-level statement kinds**: `Statement_Class` generators have an `else {
  debug; }` for unrecognized class-body statements; a new kind (past
  ctor/property/method/comment) hits it and hangs an unattended build. That
  `else` branch is where to add the new case.
- **`defined` semantics differ per bootstrap generation**: gal2 compiles
  `defined [X.P] { body }` as an attribute-*exists* probe with the body inside
  the try; gal3 backends compile an `is None` check. Since dialect-declared
  optional properties exist as None under `_0` binaries, an exists-check is
  always true — old code only worked because guard bodies crashed on the None
  and the try absorbed it. A guard body that doesn't dereference (e.g. just
  sets a flag) behaves differently under `_0` vs `_3`. Regime-proof idiom:
  `forgive { string Probe ([X.P].Some_Method); Flag = 'y'; }`.
- **`error` inside `forgive` is self-swallowing** — the forgive catches the
  error you just raised. Set a flag inside the forgive, raise outside it.
- **A `dialect` and a `class` of the same name collide** in the class-name
  registry (`Statement_Class:Names`; `dialect`/`parser`/`symbol` all
  register as derived classes). A derived-class registration no longer
  displaces a genuine class — before that fix, `class set <name>` spliced
  its members into the dialect and they vanished from every artifact in
  silence. Pinned by `bin/regress_oracle.sh`.
- **`dget` on a missing key yields null rather than raising**, so a
  `forgive` around it never fires and leaves the variable null. Guard
  counters and lookups with `dexists`.

## Code style

- Names: `Pascal_Case_With_Underscores`, starting uppercase/`_`/`$`; keywords are
  lowercase or punctuation.
- Add a language feature by declaring it in the dialect and giving it a fallback
  lowering; add per-target generators via sideways inheritance (`class set`) in
  the backend files. Runtime primitives go in `bin/Runtime.py` (+ the JS/other
  runtime equivalents).
- Comment complex transformations inline; keep new code in the idiom of the
  surrounding source.
