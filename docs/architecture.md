# gal3 Architecture

*Current as of 2026-07-13. The authoritative description of the gal3 compiler as
it actually exists. For what is done vs. in progress, see [status.md](status.md).*

## What gal is

**gal** — *general abstract language* — is a language whose compiler is written
in itself. The long-term goal is a **universal translator**: parse a program in
any source language into gal **language elements**, then generate those elements
into a valid program in any target language. The element tree is the pivot.

Two things make gal unusual:

1. **The compiler is a gal program.** The gal3 compiler is written in `.txt`
   source files (they are `.txt` only to stop editors from syntax-highlighting
   them), compiled to Python, and those Python binaries compile the same
   sources again. It reaches a **fixpoint** — the compiler built by the previous
   generation and the compiler built by the current generation are byte-for-byte
   identical. gal3 self-hosts.

2. **Abstraction is lowered, not interpreted.** A gal program is not a fixed set
   of built-in statements. High-level ("composite" or "fallback") language
   elements are *lowered* — rewritten in gal itself — down to a small set of
   **atomic** elements that every target-language generator knows how to emit.
   New abstractions are added by writing their lowering in gal, not by patching
   every backend.

### Capitalization convention

`gal`, `goalspell`, and `nsl` are always written lowercase, even at the start of
a sentence. By convention gal **keywords** are lowercase or punctuation, and gal
**names** (classes, methods, variables, properties) begin with an uppercase
letter, `_`, or `$`. gal0/1/2 enforced this; in gal3 it is only a convention.

## The lineage

| generation | role today |
|------------|------------|
| **gal1** (`gal1/`) | original bootstrap compiler. Primitive syntax. Still the root of the gal2 build. |
| **gal2** (`gal2/`, formerly *goalspell*) | the previous stable compiler. Excellent but limited. Its job now is to **bootstrap gal3** — it compiles the gal3 `.txt` sources into their first Python binaries. Being freely modified only in service of gal3; no other codebase depends on it. |
| **gal3** (`gal3/`) | the current compiler. Self-hosting since 2026-06-10. Everything below is gal3. |

**nsl** (*natural syntax language*) is a line-oriented surface variant of gal
(gal uses curly braces and semicolons; nsl uses line structure). The nsl backend
exists in the tree but is not part of the active build.

## The compilation pipeline

Every gal artifact is produced by the same multi-stage pipeline. The core bet is
that most of the work happens *before* any target language is chosen:

```
  source.txt
     │  gal stage         (galN: parse + all inference, emit gal)
     ▼
  program.gal
     │  fallback stage    (fallback: lower composite elements to gal)
     ▼   ── repeat until fixed point (typically 2–5 iterations) ──
  program.atomic          (only atomic elements remain)
     │  target stage      (galpy / galjs / galgo / galjava / galcpp / galc)
     ▼
  program.py  /  .js  /  .go  /  .java  /  .cpp  /  .c
```

1. **gal stage** — the front end. Parse the source into an element tree, run the
   full inference pipeline (below), and emit gal. Produces `program.gal`.
2. **fallback stage** — repeatedly lower composite/"fallback" language elements
   into simpler gal, re-running until the output stops changing. The result,
   `program.atomic`, contains only **atomic** elements. Sometimes several
   fallback passes are needed to reach atomic; the build loops until a pass is a
   no-op (capped at 5–6 iterations).
3. **target stage** — a per-language generator walks the atomic tree and emits
   the target source. Because the input is already atomic, each backend only
   needs to know how to emit the small atomic set plus that language's
   idioms.

This is why adding a language is tractable: a new backend is an
`<lang>_inference.txt` + `<lang>_main.txt` pair that generates the atomic
elements. It never has to understand high-level abstractions — the fallback
stage already removed them.

### Atomic vs. fallback vs. skycoding

- **atomic** elements map directly to most target languages (an integer
  assignment, an `if`, an arithmetic operation).
- **fallback / composite** elements are defined by a *lowering* into simpler gal.
  `todo`, for example, lowers to a `comment` with `"TODO: "` prepended.
- **skycoding** is Erik's term for a highly abstract element whose lowering
  isn't designed yet — it may compile to a debugger breakpoint or an error
  until its fallback is written. Abstraction first, lowering later.

## The inference pipeline

The gal stage is a sequence of **inferences** over the element tree. The driver
`Compiler.Infer` runs `Infer_Input` then `Infer_Output`
(`gal3/compiler_base.txt`):

**Front end — `Infer_Input`:**

| # | inference | does |
|---|-----------|------|
| 1 | Infer_Text | load the source text |
| 2 | Infer_Characters | text → character objects |
| 3 | Infer_Tokens | characters → tokens |
| 4 | Infer_Elements | tokens → parsed language elements |
| 5 | Infer_Components | identify component structure within elements |
| 6 | Infer_Classification | classify elements into specific language constructs |
| 7 | Infer_Attributes | assign attributes to elements |
| 8 | Infer_Appends | build relationships between elements (incl. sideways inheritance targets) |
| 9 | Infer_Ordering | establish dependency/execution order; **execute sideways inheritance** (splice `class set` members into their class) |
| 10 | Infer_Structure | build the hierarchical (owner/parent) structure |

**Back end — `Infer_Output`:**

| # | inference | does |
|---|-----------|------|
| 11 | Infer_Variables | register variable declarations and resolve references per scope |
| 12 | Infer_Type | data-type inference (see [data_type_inference.md](data_type_inference.md)) |
| 13 | Infer_Class_Structure | build class hierarchy and relationships |
| 14 | Infer_Inheritance | apply inheritance rules (esp. for targets with no class system) |
| 15 | Infer_Code | generate the target output |
| 16 | Infer_Intelligence | LLM hook (reserved; see *LLM integration* below) |

### The element-order contract

The parser produces **both** a tree (each parent's `Elements` child list) **and**
a flat list (`Parser.Elements`) in **dependency / post-order** — every element
appears after all of its children, tokens included as leaves. This contract is
load-bearing and must be honored by any generated parser:

- **Bottom-up** inferences (e.g. type inference, components, appends) iterate the
  flat list **forward** — a child has already computed its properties before its
  parent runs.
- **Top-down** inferences (structure, classification) iterate the list **in
  reverse** — an owner tells its children who owns them before they propagate
  that down.

The flat list is derived by a post-order walk of the finished tree
(`Compiler.Derive_Elements` / `Walk_Element`) **after** parsing and **before**
memoization — memoization is unsound without it.

### Sideways inheritance

A class can be defined bare in one module and *extended* elsewhere via a
`class set` / class-append that grafts a new method onto the end of the class
body. This lets a bare dialect declare statements and arguments in one place,
while separate modules add "how to generate this into Python," "…into gal," etc.,
without touching the original declaration. `Infer_Ordering` executes the splice
at the parse-tree level and re-derives the element list so members precede their
class in dependency order (single-pass bottom-up inference stays correct).

## Dialects

A **dialect** is a set of language-element declarations (statements, operations,
syntaxes, and their argument shapes and precedence). The compiler dialect
(`compiler_dialect.txt`) defines the vocabulary the compiler itself is written
in. Backends and initiatives extend the dialect rather than hard-coding syntax:
the Python-parsing work, for instance, added `python print`, `python while`,
`python for range`, and a family of `py +`/`py -`/… operations that lower to gal
atomics. New abstract elements are declared in the dialect and given a fallback
lowering; generators then only ever see the atomic result.

## Target languages

Six target languages are complete, plus a frozen C proof of concept. Each is one
`<lang>_inference.txt` + `<lang>_main.txt` pair producing a `gal<lang>.py` binary,
all structured as a 1:1 mirror of `python_inference.txt` (same generate list,
language-specific bodies).

| target | artifact | execution model | status |
|--------|----------|-----------------|--------|
| Python | `galpy` | interpreter | complete; the primary self-hosting target |
| JavaScript | `galjs` | JIT dynamic engine (node) | complete (3.0.1) |
| Go | `galgo` | native + GC | complete (2026-07-11) |
| Java | `galjava` | managed bytecode VM | complete (2026-07-12) |
| C++ | `galcpp` | native, manual memory | complete (2026-07-12) |
| MUMPS | `galmumps` | interpreted, database-native | complete (2026-07-19) — one routine per class, inheritance flattened at compile time, objects in a global |
| C | `galc` | native, manual everything | **frozen POC** — hello + main-only scalars; gal→C needs a hand-built string/collection/object runtime, deferred as future work |

The six live targets (Python, JS, Go, Java, C++, MUMPS) are validated by a
31-cell oracle over five sample programs; see
[five_languages.md](five_languages.md). Design rule: each backend handles exactly
the coverage contract of the sample programs and **fails loudly** beyond it
rather than emitting subtly wrong code.

## The artifact set

The build produces fourteen self-hosting artifacts. Every artifact is a
concatenation of shared source layers plus its own layer. The shared **zero**
stack — the abstract compiler with no front-end grammar and no backend — is:

```
compiler_base + compiler_dialect + attributes_inference
              + structure_inference + data_type_inference + llm_inference
```

| artifact | built on | what it is |
|----------|----------|------------|
| `gal` | zero + gal_base + gal_main | the gal front end: parse + infer + emit gal |
| `fallback` | zero + gal_base + fallback_inference + fallback_main | lowers composite gal → atomic gal |
| `galpy` | zero + gal_base + fallback_inference + python_inference | gal → Python |
| `galjs` | + javascript_inference | gal → JavaScript |
| `galgo` | + go_inference | gal → Go |
| `galjava` | + java_inference | gal → Java |
| `galcpp` | + cpp_inference | gal → C++ |
| `galmumps` | + mumps_inference | gal → MUMPS (a routine bundle, one routine per class) |
| `galc` | + c_inference | gal → C (frozen POC) |
| `peg` | zero + peg_base + peg_gen | reads a pegen grammar, generates a gal parser |
| `pylex` | zero + py_base | Python tokenizer |
| `pyparse` | py_base + pyparse_base + python_parser | Python parser (built by the **gal3 chain** — needs gal3's memoization + left-recursion) |
| `pygen` | + pygen_base | regenerates normalized Python from the parse tree |
| `pygal` | + pygal_base | translates parsed Python into gal |

`python_parser.txt` is itself generated during the build: `peg` reads
`grammars/python-3.11.gram` and emits the parser as gal source, which `pyparse`,
`pygen`, and `pygal` then include.

The Python-toolchain artifacts (`peg`, `pylex`, `pyparse`, `pygen`, `pygal`) are
the front half of the universal-translator vision: they let gal ingest an
external language — Python — into the same element tree the gal front end
produces. See [peg_python_parsing_design.md](peg_python_parsing_design.md).

## The build chain and self-hosting

Three scripts in `gal3/`, run in order, establish the fixpoint:

1. **`./build`** — the gal2 compiler (`~/.goalspell/goalspell`) compiles the
   `.txt` sources into `~/.gal3/{artifact}.py`. This is the bootstrap: gal2
   builds gal3.
2. **`./selfbuild`** — those gal3 binaries compile the *same* sources into
   `~/.gal3/{artifact}_3.py`. gal3 builds gal3.
3. **`./selfself`** — the `_3` binaries rebuild once more into
   `{artifact}_33.py`. gal3, built by gal3, builds gal3.

Self-hosting is proven when **`_3` and `_33` are byte-identical** for all fourteen
artifacts. gal2 dropping out of the loop cannot change the output. Build
artifacts land in `~/code/gal3build/`; the runnable binaries in `~/.gal3/`.

`./fullbuild` (repo root) runs the whole gal1→gal2→gal3 chain from scratch. Fast
per-artifact iteration scripts exist for the Python toolchain (`./pybuild`,
`./pegbuild`, `./pyparsebuild`, `./pygenbuild`, `./pygalbuild`) and for the
backends whose edits stay in one layer (`./galjavabuild`, `./galmumpsbuild`).

## Hosting the compiler in another language

A *target* is a language gal can emit. A **host** is a language the compiler
itself runs in — a strictly stronger claim, because the compiler is the most
demanding gal program there is, and because it can be checked absolutely: the
hosted edition must rebuild every pipeline stage byte-identically to the
Python-hosted chain.

| host | since | gate | what it proves |
|------|-------|------|----------------|
| Python | 3.0.0 (2026-06-10) | `./build && ./selfbuild && ./selfself` | the reference chain; the fixpoint |
| JavaScript / node | 3.1 (2026-07-16) | `./jsself` | 12 artifacts rebuilt byte-identically at every stage, plus the JS fixpoint |
| Java / JVM | 3.2 (2026-07-18) | `./javaself` | the same 12 rows through `javac` + a reflective runtime |
| MUMPS / YottaDB | 3.3 (2026-07-19) | `./mumpsself` | `gal`, `fallback`, `galpy` run as routine bundles; the chain rebuilds the compiler's own source at every stage |

Each host forced a different question about what gal means. node needed
`Gal_New` proxies to reproduce Python's `AttributeError`; the JVM needed
hoisting and reflective dispatch; MUMPS — which has no objects, no exceptions
in the usual sense, and only one data structure — needed compile-time
inheritance flattening (each class becomes one routine of flattened labels,
which *is* the vtable), handle-based collections for reference semantics, and
a decision about what `None` means in a language whose empty string is its
null. See [js_selfhost_design.md](js_selfhost_design.md),
[java_selfhost_design.md](java_selfhost_design.md), and
[mumps_design.md](mumps_design.md).

### Standard debug loop

```
./build && ./selfbuild && python -m py_compile ~/.gal3/*_3.py && ./selfself
diff ~/.gal3/gal_3.py ~/.gal3/gal_33.py      # (and the other 12) — must be empty
```

The fixpoint diff is a **structural** check: it catches a change that isn't
stable under self-compilation, but two consistently-wrong generations still
diff clean. Behavior is checked separately by the oracles
(`gal3/bin/*_oracle.*`), which compare real program output against ground truth.

## Runtime

Generated programs call into a small runtime (`gal3/bin/Runtime.py`, plus JS/other
equivalents) for primitives that are easier to provide than to inline —
`Readline()`, `Chr()`, file helpers, and so on. Backends pull in runtime
dependencies through a module include mechanism (`Module.Add_Include`) that
dedups imports, so a generated program only imports what it actually uses.

## Debugging

There is no gal-level debugger; **you debug in the target language.** The usual
loop is to run the generated Python under `zdebug` (a Python debugger kept in
`gal3/bin/zdebug.py` and installed to `~/.gal3/`), or to `import` a compiled
artifact as a module and introspect its element tree directly. A `debug;`
statement in gal lowers to a `zdebug.zbreak()` breakpoint. Because `debug;` can
silently swallow errors during an unattended build, a standard trick is to
temporarily stub `~/.gal3/zdebug.py` with a no-op `zbreak` to see the real
failure — then restore it so real `debug;` statements fire loudly again. JS and
other targets are debugged with their native debuggers.

## LLM integration (`llm_inference`, `Infer_Intelligence`)

The `llm_inference.txt` layer and the `Infer_Intelligence` stage are the
reserved seam for LLM-assisted inference — the point where a model could be asked
to lower a *skycoded* element, propose a data type, or generate an idiom that no
rule handles yet. The methodology (probe → LLM-infer → human-proof → capture as a
test case → replace with fast code where possible, keeping the LLM for the hard
cases) is described in [inference_process.txt](inference_process.txt). It is a
seam in the architecture, not the load-bearing path: the compiler self-hosts and
generates all six targets with traditional rule-based inference.

## Where to read next

- [status.md](status.md) — done / in progress / next, with pointers.
- [data_type_inference.md](data_type_inference.md) — how types flow to typed targets.
- [five_languages.md](five_languages.md) — the 5-programs × 5-targets oracle.
- [peg_python_parsing_design.md](peg_python_parsing_design.md) — parsing external Python.
- `gal3/CLAUDE.md` — day-to-day build/debug guidance for working in the tree.
