# The gal3 compiler: overview and thesis

*Chapter 1 of the gal3 compiler design documentation — the basis for a paper
comparing gal3's architecture with conventional compiler and transpiler
design. Everything asserted here is elaborated, with `file:line` evidence, in
chapters 2–13.*

## What gal3 is

**gal** — *general abstract language*, always lowercase — is a language whose
long-term goal is a **universal translator**: parse a program in any source
language into gal *language elements*, then generate those elements into a
valid program in any target language. The element tree is the pivot.

As of mid-2026 the gal3 compiler:

- **self-hosts** — thirteen artifacts reach a byte-identical
  self-compilation fixpoint (`_3 ≡ _33`), with gal2 reduced to a bootstrap
  step (3.0.0, 2026-06-10; JavaScript a second self-hosting target since
  3.0.1);
- generates **five complete target languages** — Python, JavaScript, Go,
  Java, C++ (plus a frozen C proof of concept) — validated by a 26-cell
  oracle requiring byte-identical program output across targets;
- **parses external Python 3.11** (49/49 compatible stdlib modules, at
  CPython's acceptance boundary) into the same element trees, translates it
  to gal, and round-trips it behaviorally byte-exactly — the front half of
  the universal-translator vision;
- is **extensible by plugins written in gal3** and compiled into the
  compiler, the first being a Documentation dialect whose articles execute
  their own demos.

## One program, end to end

```gal
module Fizzbuzz
{
    main
    {
        for I range 1 20
        {
            if ((I mod 15) = 0)      { say "FizzBuzz"; }
            else if ((I mod 3) = 0)  { say "Fizz"; }
            else if ((I mod 5) = 0)  { say "Buzz"; }
            else                     { say I; }
        }
    }
}
```

The pipeline every program (and the compiler itself) travels:

```
source.txt
   │  gal stage        parse + all sixteen inferences, emit normalized gal
   ▼
program.gal
   │  fallback stage   lower composite elements to simpler gal — repeat
   ▼                   until byte-stable (typically 2–4 passes)
program.atomic         only atomic elements remain
   │  target stage     one generator per atomic element per language
   ▼
program.py / .js / .go / .java / .cpp
```

Every stage's input and output is gal *text*; every stage re-runs the full
parse-and-infer pipeline. The oracle runs all five outputs and requires their
program output to be byte-identical.

## The innovations, in one paragraph each

**Characters and tokens are first-class objects** (ch. 2). Every character
of source text becomes a heap object in a class hierarchy
(`Char_Upper`, `Char_Quote`, …); tokens grow by asking each token object
whether it will absorb the next character. There is no lexer formalism — and
no separate extension mechanism for lexing. This is also the single largest
reason the compiler is slow, a cost accepted deliberately for uniformity.

**Parsing is decoupled from classification** (ch. 3). The grammar recognizes
only *shape* — statement, `(operation)`, `[syntax]`, `{block}` — in ~50
declared lines with no keywords in them. A separate pass looks up each
element's keyword sentence in a dialect dictionary (longest match wins) and
attaches a construct-specific *classification object*. The construct
inventory is data, not grammar; unknown verbs parse fine and are counted,
not rejected.

**Compilation is a sequence of inferences over one element population**
(ch. 4). Sixteen inference stages each *add* information to the same
elements; per-construct behavior is a method on the element class, not a
case in the pass. One flat post-order element list serves every stage:
forward = bottom-up, reverse = top-down — the element-order contract.

**Abstraction is lowered, not interpreted** (ch. 5). Composite elements are
defined by fallback lowerings written in gal, applied by whole-program
re-emission until a byte-stable fixpoint. "Atomic" is not a flag — it is
a fixpoint of parse∘emit. Even the compiler's own generator and
grammar constructs are composites that lower themselves. Elements with no
lowering yet ("skycoding") flow through harmlessly until a backend needs
them.

**Sideways inheritance** (ch. 6). `class set` appends members to a class
declared elsewhere, executed as a parse-tree splice by inference #9. It is
the packaging mechanism for the whole codebase: fallback rules, all backend
generators, and inference passes are method grafts from separate files onto
one shared element hierarchy — both axes of the expression problem stay
open.

**Dialects: the language as data** (ch. 7). Statements, operations, and
syntaxes are *declared*; declarations compile into element classes with
generated argument binders, and precedence and result types ride the same
declaration-property channel. There are no reserved words; a dialect is
selected per compiler instance; new constructs need a declaration plus a
lowering — never parser changes, and usually zero backend work.

**Backends implement a small atomic contract** (ch. 8). A backend is one
file of `generate` bodies — 143 elements for the self-hosting targets, an
identical 59-element subset for Go/Java/C++ — each grafted as an
`Infer_<Lang>` method. The atomic "IR" is still syntax-shaped, which is what
makes *idiomatic* target output tractable; backends are explicitly partial
and **fail loudly beyond the contract** rather than emitting subtly wrong
code.

**A four-generation bootstrap, fully preserved** (ch. 9). gal0 (Raku, 2021)
→ gal1 (prefix syntax) → gal2/goalspell (keyword-resolved syntax) → gal3;
one command replays the whole ancestry from source. The verification
discipline separates *structural* stability (the byte-exact fixpoint) from
*behavioral* correctness (output oracles) — and the LLM-centric design gal3
started from was displaced by exactly this deterministic discipline.

**Type inference for translation, not checking** (ch. 10). Two inferred
properties — definitional `Data_Type`, contextual `Usage` — feed five type
systems from one pass. Mismatch is a conversion decision, not an error;
unknowns convert nothing, which let the analysis land provably
behavior-neutral under the fixpoint.

**The universal-translator front half** (ch. 11). A parser generator (`peg`)
turns CPython's own PEG grammar into a gal parser (packrat memoization and
Warth-style left recursion live in the engine, generated around every rule);
a gal tokenizer reproduces CPython byte-for-byte; parsed Python is
*classified* into a Python dialect of gal whose fallback lowerings are the
single semantic equivalency point; round trips are verified behaviorally,
including on the compiler's own generated artifacts.

**Plugins and the LLM seam** (ch. 12). Plugins are gal source spliced by a
staged `include` mechanism and compiled by the fixpoint kernel; the first
plugin is a Documentation dialect whose articles run their own demos and
gate publication on drift. A reserved inference stage (`Infer_Intelligence`)
holds the LLM's place in the pipeline; today the LLM's role is a development
methodology (probe → infer → proof → capture → replace), not an execution
path.

## The honest costs

The paper should claim the trade-offs as consciously purchased:

- **Speed.** Object-per-character lexing, full re-inference every fallback
  pass, and dictionary-driven classification make compilation orders of
  magnitude slower than conventional compilers; megabyte-scale parse time is
  an open item. The bet: compiler throughput matters less than architecture
  uniformity for a research translator. The gal compiler was designed to be
  a symbolic AI program rather than a conventional language compiler, so the
  decision to sacrifice execution speed for generality and power was made
  early in the toolchain.
- **Static guarantees.** No type checker over the compiler, no exhaustive-
  match enforcement, per-token classification objects. The substitutes are
  empirical and total: the byte-exact fixpoint, the output oracles, and a
  loud-failure discipline (`error`, `debug;`) at every coverage edge.
- **Deliberate partiality.** Backends and the Python translator cover
  explicit contracts and refuse the rest — completeness is traded for
  the guarantee that what compiles is behaviorally exact.
- **No backwards compatibility.** The concept of backwards compatibility
  was explicitly discarded in the development of gal1. If a program works
  today, there is no guarantee that the behavior will be exactly the same
  in the future.

## Reading order

| # | chapter | innovation |
|---|---|---|
| 2 | characters and tokens | lexing as object protocol |
| 3 | parsing and classification | shape grammar + dialect dispatch |
| 4 | the inference pipeline | inferences × element classes |
| 5 | fallback lowering | composite → atomic by re-emission to fixpoint |
| 6 | sideways inheritance | `class set` and its sugar family |
| 7 | dialects | the language as data |
| 8 | backends and atomics | the five-target contract |
| 9 | bootstrap lineage | gal0→gal3, fixpoint + oracle |
| 10 | type inference | Data_Type / Usage |
| 11 | universal translation | the Python-ingestion toolchain |
| 12 | plugins and the LLM seam | extending the compiler in gal |
| 13 | theory comparison | the systematic compare/contrast |
