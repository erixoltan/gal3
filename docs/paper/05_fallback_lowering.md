# Fallback lowering: abstraction compiled away in the language itself

*Chapter 5 of the gal3 compiler design documentation. Sources:
`gal3/fallback_inference.txt` (the ~150 lowering rules + `Fallback_Compiler`),
`gal3/fallback_main.txt`, `gal3/build:44–73` (the fixpoint loop), the build
artifacts `~/code/gal3build/fallback_3.{gal,fb0,fb1,fb2,fb3,atomic}`.*

## The idea

gal has no fixed statement set. A high-level ("composite" or "fallback")
element is defined by a **lowering written in gal**: a rule that re-emits the
element as simpler gal source. Lowerings are applied repeatedly until the
program contains only **atomic** elements — the small set every backend
generates directly. New abstractions are added by writing one lowering, never
by touching backends.

```
program.gal ──fallback──▶ fb0 ──fallback──▶ fb1 ──▶ … ──▶ program.atomic
                 (repeat until two consecutive outputs are byte-identical)
```

## Mechanism: source-to-source re-emission, not tree rewriting

The crucial design fact: fallback is **not** an in-memory tree-rewriting
pass. Each pass is a *whole-program re-emission*:

1. Parse the gal source and run the **entire** inference pipeline (all of
   chapter 4 — characters, tokens, elements, classification, structure,
   variables, types).
2. Render every element back to gal *text*, bottom-up over the post-order
   flat list. Composite elements render as their simpler equivalents;
   atomic elements render as themselves.
3. Write the text to a file. A bash loop (`build:44`, `atomic()`) feeds it
   back into the same compiler until `cmp -s` says two consecutive outputs
   are byte-identical (capped at 5–6 iterations).

The rewrite "engine" is nothing more than string-returning `Infer_Fallback`
methods plus the shell loop. Text is the only interchange format between
passes; each pass is a fresh OS process. `Fallback_Compiler.Infer_Code`
(`fallback_inference.txt:1573`) runs `Infer_Gal` first (the identity
pretty-printer from `gal_base.txt`) so the default rule has something to
read, then `Infer_Fallback`; the `Program` root's `Fallback` string becomes
the output file.

The generic rules make *unhandled* elements atomic by default
(`fallback_inference.txt:134–203`):

```gal
generate Element [my Gal];                      // identity via the gal rendering
generate Statement { string Code [my Verb] (i Fallback_Arguments) (i Fallback_Block); ... }
```

"Atomic" therefore has no flag or registry anywhere in the code — an element
class is atomic iff it is **a fixpoint of parse∘emit**. The atomic vocabulary
is exactly the set of elements that survive the loop, and the per-target
generate lists (chapter 8) implement exactly that surviving set.

## Example lowerings, trivial to meta

**Trivial** — `todo` (`fallback_inference.txt:1339`):

```gal
generate Statement_Todo
    'comment "TODO: "' (i Fallback_Arguments) ';';
```

**Control-flow sugar** — `break if`, `verbose`/`verbosity`:

```gal
generate Statement_Break_If
    'if' (i Fallback_Arguments) ' { break; }';
```

`verbosity;` lowers to `flag Verbose [false];` and each `verbose ...;` to
`if Verbose { say ...; }` — debug tracing is a *language feature with a
lowering*, not a runtime facility.

**Formatting composite** — `flowerbox` computes the box (widest line,
padding, star borders) *at lowering time* and emits a single `comment`
statement. The work happens once, in the compiler, in gal.

**Cross-language semantics** — the Python-dialect elements (chapter 11).
gal has no `while`, so:

```gal
generate Statement_Python_While
{
    comment `gal has no while loop: forever with an inverted break`;
    string Code 'forever' [line] '{' [line]
        [indent] 'break if (not ' [my Condition Fallback] ');' [line]
        (i Fallback_Statements)
        '}';
    i = Code;
}
```

And Python's polymorphic `+` is lowered **type-directedly** — the lowering
consults the inferred types (chapter 10) and *records its decision* so
enclosing operations see it in the same bottom-up pass:

```gal
generate Operation_Python_Add
{
    ...
    if Stringish { my Data_Type = 'string'; i = (append '(append ' ... ')'); }
    else         { my Data_Type = 'number'; i = (append '(' ... ' + ' ... ')'); }
}
```

**Class-producing composites** — a one-line `symbol` declaration lowers to a
full class (properties + constructor + initializer). `dialect` blocks lower to
`Dialect_<Name>` classes; `statement`/`operation`/`syntax` declarations lower
to element classes with generated `Attributes` binders (chapter 7).

**Meta** — the most striking case: **the generator machinery lowers itself.**
`generate X {...}` is a composite statement whose fallback rewrites it into
`class set X { method flag Infer_<Lang> {...} }`; `generator Lang Ancestor
{...}` lowers into a `<Lang>_Generator` class with a synthesized driver loop;
`inference X { handle C {...} }` lowers into `class set C { method flag
Infer_X {...} }`; and the grammar DSL (`sequence`/`either`/`repeating`)
lowers into packrat-memoized parse methods, including the entire left-
recursion seed-growing wrapper emitted as gal text
(`Fallback_Memo_Wrapper`, `fallback_inference.txt:45–84`). There is no
interpreter for any of these constructs — the compiler's own most powerful
features are ordinary composite elements defined by lowerings.

## The fixpoint, measured

The build artifacts show the fallback compiler's own convergence:
`.gal` → `fb0` (428 KB) → `fb1` (410 KB) → `fb2` (411 KB) → `fb3`
(byte-identical → stop). Three productive passes plus one confirming pass:

- **pass 1**: all first-order lowerings (`todo`→comment, `generate`→
  `class set`, declarations→classes, grammar→parse methods).
- **pass 2**: the `class set` blocks emitted by pass 1 are spliced into their
  primary classes by `Infer_Ordering` (chapter 6), and composites *inside
  pass-1-generated code* (the `verbose` calls in the synthesized driver, the
  `break if` in the memo wrapper) get lowered.
- **pass 3**: formatting residue only — inline `{ break; }` re-parses as a
  block and pretty-prints canonically. Normalization is part of reaching the
  fixpoint, which is what lets the convergence test be a bare `cmp -s`.

A program using only first-order sugar converges in one productive pass; the
compiler itself — whose lowerings *emit further composite code* — is the
observed three-pass worst case.

## Failure posture and skycoding

- A lowering that throws is caught per-element by the generated driver;
  the element's `Error` is recorded, no output file is written, and the
  missing file stops the shell loop.
- Fallback refuses input containing `include` — "a file that still contains
  one when it reaches fallback was not produced by the gal compiler. fail
  loudly instead of passing it downstream" (`fallback_inference.txt:1417`).
- **Skycoding** — Erik's term for inventing an abstract element *before* its
  lowering exists ("Abstraction first, lowering later"). The layers respond
  gracefully in sequence: an *undeclared* verb self-classifies and is counted
  in the unclassified-verbs report; a *declared* element with no lowering
  passes through every fallback pass verbatim (it inherits the generic
  re-emitter — it is a fixpoint without being in any backend's vocabulary);
  only at the **target stage** does it bite, where the backend's catch-all
  raises `Class X doesn't implement Infer_Python` with source excerpt. The
  reserved LLM seam (`Infer_Intelligence`, chapter 12) is positioned exactly
  here: the point where a model could be asked to lower a skycoded element
  no rule handles yet. The language-reference example is
  `pay Gratitude to Supporters of Person;` — a statement that can be
  *written and parsed today* and given meaning later.

## Conventional theory comparison

| aspect | conventional design | gal3 fallback |
|---|---|---|
| desugaring | fixed early pass inside the compiler (e.g. GHC's desugarer, Scheme's macro expansion) mapping surface syntax to core IR | open set of lowerings, written in the language, applied by whole-program re-emission to fixpoint |
| macro expansion | per-call-site tree substitution at parse/expand time; hygiene machinery | per-class re-emission after *full semantic inference* — a lowering can consult inferred types, scopes, and structure |
| IR lowering | progressive lowering through IR levels (HIR→MIR→LLVM; MLIR dialects) | one representation (gal source) at every level; "level" = which composite classes remain |
| staging | expansion inside one compiler process | each pass is a separate process; text files are the interchange; fixpoint checked with `cmp` |
| termination | macro expansion may not terminate; recursion depth limits | iteration cap + byte-equality; convergence is observable in the `.fb*` artifacts |
| unknown constructs | error at first use | flow through untouched (skycoding); fail loudly only at the last stage that truly needs them |

Framing points for the paper:

- **The closest relative is MLIR's dialect-lowering philosophy** —
  progressive lowering through named abstraction levels, extensible by
  users — but gal3 collapses the representation stack: source language, every
  intermediate level, and the backend input are all *gal text*, differing
  only in which element classes appear. Anyone who can read gal can read
  every compilation stage, and any stage can be dumped, diffed, edited, and
  re-fed.
- **Lowering after inference is the power move.** Conventional desugaring
  runs before type checking, so sugar cannot be type-directed without
  special-casing. gal3 runs the whole inference pipeline every pass, so a
  lowering like `py +` can dispatch on inferred operand types — semantic
  macro expansion, bought at the cost of re-running inference per pass.
- **Fixpoint-as-normal-form.** Reaching atomic form by "iterate until
  byte-stable" treats the term-rewriting notion of normal form completely
  literally, with confluence and termination checked *empirically* per build
  (cap + cmp) rather than proven. This is of a piece with the project's
  general stance: replace static guarantees with cheap total observations
  (chapter 9).
