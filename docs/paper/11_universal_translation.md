# Toward a universal translator: parsing Python into gal

*Chapter 11 of the gal3 compiler design documentation. Sources:
`gal3/peg_base.txt`, `peg_gen.txt`, `py_base.txt`, `pyparse_base.txt`,
`pygen_base.txt`, `pygal_base.txt` (3,161 lines), the generated
`python_parser.txt` (3,686 lines), `docs/peg_python_parsing_design.md`,
`docs/status.md`.*

## The vision, and its first realized half

> "gal is intended to serve, eventually, as a universal translator: parse a
> program in any source language into gal language elements, then generate
> those elements back into a valid program in any target language. **The
> element tree is the pivot.**" — `docs/peg_python_parsing_design.md`

Chapters 5–8 describe the *output* half: gal elements → five target
languages. This chapter describes the *input* half, realized for Python:
five artifacts that ingest external Python 3.11 into the same element trees
the gal front end produces, and back out.

| artifact | function | validation |
|---|---|---|
| `peg` | reads a pegen grammar (`grammars/python-3.11.gram`), **generates a gal parser as gal source** | all 229 rules parsed; construct counts exact |
| `pylex` | stateful Python tokenizer in gal (INDENT/DEDENT, joining, prefixes) | 50/52 stdlib modules byte-identical vs. CPython `tokenize` |
| `pyparse` | drives the generated parser over the token stream | 49/49 3.11-compatible stdlib modules; CPython's acceptance boundary |
| `pygen` | regenerates normalized Python from the parse tree | 49/49 on ast-equality + comment-multiset + idempotence |
| `pygal` | translates the parse tree into gal (via a Python dialect) | behavioral round-trip, two generations deep |

All five participate in the 13-artifact self-hosting fixpoint. Notably,
`pyparse` is **the first artifact gal2 structurally cannot build**: packrat
memoization and left-recursion seed-growing exist only in gal3's parser
generators, and Python's grammar is pervasively left-recursive — a concrete
demonstration that gal3 exceeded its bootstrap parent.

## `peg`: a parser generator whose output is gal source

`peg` parses the pegen metagrammar with the only hand-written parser of the
initiative (~30 rules in gal's parser DSL, `peg_base.txt:251`), then walks
the grammar's element tree emitting **gal parser DSL text** — the same
`parser`/`sequence`/`either` statements the gal front end itself is written
in (chapter 7). Core transform, from the file header:

> "rule lifting: every nested group, optional group, gather and
> multi-alternative body is hoisted into a synthetic named rule, because gal
> rules reference only names and literals. Erasures that preserve
> recognition semantics: actions and type annotations are dropped; cut and
> forced degrade to nothing / plain match; invalid_ rules … are filtered
> out."

Postfix operators map mechanically (`e?`→`[optional e]`, `e*`→`[optrep e]`,
`e+`→`[repeating e]`); gathers (`sep.e+`) expand into element+tail pairs;
lookaheads are hand-emitted save/parse/restore methods; the pegen NAME rule
gets a keyword-exclusion method. The generated `python_parser.txt` (marked
DO NOT EDIT) contains 416 sequences, 125 eithers, 61 lookahead methods —
and then **541 class declarations**: every grammar rule *is* an element
class (`class Python_t_primary is Py_Rule;`), so the parser's output is
directly the element-tree representation the whole compiler operates on.

### Packrat + left recursion live in the engine, not the grammar

Nothing in `python_parser.txt` mentions memoization. The gal3 fallback stage
wraps **every** generated parse rule in a memo wrapper
(`Fallback_Memo_Wrapper`, `fallback_inference.txt:45`), and the runtime
lives in `compiler_base.txt:1394–1596` (chapter 3): plant an in-progress
seed, run the rule; a rule that re-enters its own seed at the same position
is left-recursive — fail that attempt so a base case can win, then *grow*
the seed by re-running while the match keeps advancing (Warth), invalidating
only **same-position** memo entries between iterations ("positions only move
forward in a parse, so an entry at a later position can never consult a seed
at an earlier one") — the position-scoping insight that took regrowth from
catastrophic (464 s/file) to ~6 s/file. Detection is fully dynamic: no
grammar annotation marks recursion, and the machinery costs nothing when it
never fires (gal's own grammar: fixpoint held byte-exact).

### The element-order contract, stress-tested

Python's PEG grammar backtracks heavily *after* successful sub-parses, and
memo replay pushes cached elements at arbitrary moments — so the historical
"flat list = parse chronology" equivalence breaks completely. The design
decision (chapter 3): **derive the flat list, don't accumulate it** — one
post-order walk from the root after parsing; orphans from lost alternatives
and discarded grow iterations vanish because they are unreachable.
"Memoization is unsound without it." Failed parses still report precisely
via `High_Water`, the farthest consumption point, which survives rollback.

## `pylex`: the irregular part of Python, as object protocol

The grammar-expressible part of Python lives in `.gram`; everything CPython
handles in its tokenizer lives in `Py_Compiler`'s line discipline
(`py_base.txt:409`): the indentation stack (tabs advance to multiples of 8,
CPython's rule), implicit joining inside brackets, explicit backslash
joining, blank-line suppression, and synthesized
INDENT/DEDENT/NEWLINE/ENDMARKER. Token shapes reuse the
`Factory`/`Append_Character` pattern of chapter 2 — e.g. `Py_Number` absorbs
an `e` only when a digit follows, "so `1else` lexes as NUMBER 1 then NAME
else"; string prefixes (`r`, `f`, `rb`…) lex as NAMEs and are **merged
retroactively** when a quote follows with no gap. Comments and non-logical
newlines go to a parallel `Trivia` list preserved for later comment
attachment. The 3.11 pin makes f-strings opaque STRING tokens; the two
stdlib failures are PEP-701 constructs 3.11 itself rejects — "the pin
working as designed."

## `pygen`: normalization with mechanical semantics checks

Because the parse tree is a full CST that kept every token, **one generic
generator body covers all 541 classes**: concatenate children under a
token-pair spacing policy (`Normpy_Glue`), with `Py_Indent`/`Py_Dedent`
leaves opening and closing 4-space interior captures. A handful of
tight-spacing overrides (factor, power, slice, `x=3` vs `x: int = 3`)
complete it. Comments reattach by a three-case heuristic (trailing / leading
/ floating out of brackets). The oracle is worth stating for the paper:

1. **ast**: `ast.dump(original) == ast.dump(normalized)` — CPython itself
   certifies meaning-preservation;
2. **comments**: every comment survives as a multiset;
3. **idempotence**: normalizing the output reproduces it byte-for-byte.

49/49 stdlib modules pass all three.

## `pygal`: Python elements → gal elements

`pygal` mirrors the gal compiler's own architecture on foreign input:
parse → **classify** → emit. One forward pass over the post-order list
builds a small semantic tree of `Pyc_*` nodes; the default handler is
*transparent adoption* — an element with exactly one classified child adopts
it, which collapses Python's deep `expression → disjunction → … → atom`
grammar plumbing for free. Unsupported constructs become `Pyc_Group`s that
**fail loudly at their own location** at emission.

The target is a **Python dialect of gal** (chapter 7): `python print`,
`python while`, `python for range`, and operations `py +`, `py mod`,
`py fstr`, `py slice`, `py list`… — each carrying Python semantics. The
fallback stage is then "the equivalency point between python semantics and
gal semantics": `python while` → `forever { break if (not C); ... }`,
`python print A B` → `say A ' ' B;`, `py fstr` → `append`, and `py +`
lowering type-directedly (chapters 5, 10). A future target that disagrees
with a lowering overrides those same classes — never the translator.

Details that make the translation *stable*, not merely correct:

- **Inverse idiom mapping**: pygal recognizes the *compiled shapes of gal's
  own statements* and maps them back — the `if X is None: raise` guard
  becomes `defined`/`undefined`, `except Exception: pass` becomes `forgive`,
  the open/read/close triple becomes `fread`, `d.items()` loops become
  `iterate`, `range(..., X + 1)` is recognized as gal's inclusive-range
  marker and stripped ("keeps round trips from accreting +1-1 chains"),
  `zdebug.zbreak()` becomes `debug;`.
- **Name mapping**: names already valid in gal pass through, so
  machine-generated Python round-trips readably; others get a `Py_` prefix;
  attribute names are never mapped (builtins like `append` must survive).
- **F-string interiors are sub-parsed** by a child compiler through the
  generated parser's expression entry point, then classified with the same
  machinery.
- Scoping is reconstructed: first assignment in a scope emits a `variant`
  declaration; `self.x` becomes `my x`.

## Verification: the round trip

Three layered oracles:

1. **`pygal_oracle.py`** — behavioral: CPython runs the original; then
   pygal → gal → fallback-to-fixpoint → galpy → CPython runs the result;
   stdout must match **byte-for-byte**. Then the loop *recurses*: the
   generated Python is fed back through the whole chain (generation 2) and
   must match again — the translator must be able to eat its own output.
2. **`pygal_artifact_oracle.sh`** — the real-artifact loop: take a
   gal3-generated artifact (the 226 KB `pylex.py` itself), translate it back
   to gal, recompile, and run both on real inputs — byte-identical token
   dumps on stdlib files. The compiler's own components survive the round
   trip.
3. **The standing fixpoint** — every dialect/lowering change re-verifies all
   thirteen artifacts.

The behavioral loop proved its worth beyond the translator: it flushed out
six latent gal3 codegen bugs *invisible to the structural fixpoint*,
including a genuine `(1+2)*3 → 7` precedence miscompilation — the concrete
case for the fixpoint/oracle dichotomy of chapter 9.

Known remaining gaps are cataloged rather than papered over
(`docs/status.md`): with-open write idiom, keyword arguments, decorators
beyond classmethod, method return types at call sites (needs a method
registry), chained comparisons (explicitly rejected: `a < b < c` evaluates
`b` once, which a naive fold would not preserve), multiple inheritance,
megabyte-scale parse time.

## Conventional theory comparison

| aspect | conventional design | gal3 |
|---|---|---|
| source-to-source translators | per-pair tools (2to3, j2objc, c2rust); shared-AST families rare | one pivot representation; N front ends + M back ends for N×M pairs — the UNCOL ambition at source level |
| parser generators | emit host-language code (yacc→C, ANTLR→Java) | `peg` emits *gal parser DSL*, compiled by the same compiler it extends; grammar rules become element classes |
| left recursion | grammar rewriting, or Warth-style support in the engine (pegen uses its own memoized scheme) | Warth seed-growing with dynamic detection + same-position invalidation, generated around every rule |
| semantic gap handling | translator special-cases each idiom | a *dialect* of semantics-carrying elements + fallback lowerings as the single equivalency point |
| fidelity testing | test suites, manual review | ast-equality via CPython, idempotence, byte-exact behavioral round trips incl. self-application |
| lossy vs lossless | most transpilers drop comments/format | CST keeps every token; trivia preserved and reattached; normalization is the *defined* output |

Framing points for the paper:

- **The UNCOL objection was about IR fidelity; gal3's answer is dialect
  layering.** The classic argument against universal pivots is that
  language-pair semantics leak through any fixed IR. gal3 doesn't pretend
  Python fits the compiler dialect directly: it *extends the dialect* with
  elements that carry Python's semantics verbatim, and concentrates the
  semantic commitment in ~30 auditable fallback lowerings. The pivot is
  extensible per source language; only the atomic set is universal.
- **Self-application as the honesty test.** Round-tripping toy programs
  proves little; round-tripping the compiler's own 226 KB generated
  artifacts, and requiring the translator to consume its own output for a
  second generation, is a materially stronger criterion — and it reuses the
  self-hosting infrastructure the project already had.
- **The pipeline reuses every architectural piece**: characters-as-objects
  (pylex), the parser DSL + memo engine (peg/pyparse), classification
  (pygal's `Pyc_*` pass is the dialect classifier aimed at foreign trees),
  dialects (the Python element stratum), fallback (the equivalency point),
  type inference (`py +`), and the oracles. The universal-translator half
  was built almost entirely out of mechanisms chapters 2–10 already
  describe — which is the strongest available evidence that the architecture
  generalizes.
