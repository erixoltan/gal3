# Parsing decoupled from classification

*Chapter 3 of the gal3 compiler design documentation. Sources:
`gal3/compiler_base.txt` lines 533–1086 (`Spell`, `Statement`, `Operation`,
`Syntax`, `Dialect`), lines 1394–1596 (`Parse_Memo`, `Parser`), lines
2014–2039 (`Infer_Classification`); `gal3/gal_base.txt` (the gal grammar).*

## The core decoupling

Most compilers parse straight into a construct-specific AST: the grammar rule
for `if` builds an `IfNode`, the rule for assignment builds an `AssignNode`.
The grammar and the language's construct inventory are the same artifact — to
add a construct you change the grammar.

gal3 splits this into **two independent stages**:

1. **Parsing** recognizes only *shape*. The parser knows that
   `... ... ... ;` is a `Statement`, `(...)` is an `Operation`, `[...]` is a
   `Syntax`, and `{...}` is a `Block`. It does **not** know what an `if` is.
   The output is a tree of generic *parse elements*.
2. **Classification** (inference #6) decides *meaning*. A separate pass looks
   at the keywords inside each generic element, consults the **dialect** — a
   dictionary from verb phrases to element classes — and attaches a
   construct-specific *classification object* to the parse element.

The consequence: **the set of language constructs is data, not grammar.** New
statements, operations, and syntaxes are added by declaring them in a dialect
(chapter 7), never by touching the parser.

## Stage 1: shape parsing

### The four shapes

All parse elements derive from `Spell is Element` (`compiler_base.txt:596`),
which carries the component lists every shape shares:

```gal
class Spell is Element
{
    property list Elements;      // raw parsed children
    property string Keyword;
    property list Keywords;      // keyword *token objects*
    property list Key_Words;     // keyword *texts*
    property list Words;         // non-keyword identifier texts
    property list Arguments;     // children minus boundaries
    property list Listargs;      // arguments minus the recognized verb
    property object Dialect;
}
```

The shapes are punctuation-driven:

| shape | surface form | class |
|---|---|---|
| statement | `words and args ... ;` optionally ending in `{ ... }` | `Statement` |
| operation | `( ... )` | `Operation` |
| syntax | `[ ... ]` | `Syntax` |
| block | `{ ... }` | `Block` |
| program | whole file | `Program` |

Each shape has an `Infer_Components` method that derives its component lists
from its raw children (inference #5). For example `Statement.Infer_Components`
(`compiler_base.txt:744`) pops a trailing `Block` off the child list (creating
an empty one if absent — every statement has a block), and copies the rest
into `Arguments`/`Listargs`. `Operation` and `Syntax` just drop boundary
tokens. Even *component identification* is a polymorphic inference step, not
parser logic.

### The parser proper

The `Parser` class (`compiler_base.txt:1415`) is a token-stream machine with
four primitive moves — `Top_Token`, `Parse_Token` (match an expected text),
`Consume_Token`, and `Rollback`. The gal grammar itself is ~50 lines of
`parser`/`sequence`/`either` *declarations* in `gal_base.txt:49–99` (chapter
7 shows them in full) that the fallback stage compiles into recursive-descent
methods over these primitives — and **grammar rule names are element class
names**: `sequence Statement` constructs `new Statement`, so the grammar's
output is directly the element tree. (`Gal_Compiler` also overrides
`Infer_Tokens` to drop whitespace tokens — gal is whitespace-insensitive at
the grammar level, and Python is not, which is why the Python toolchain
overrides the same hook the other way.) Two engine features are notable:

- **`High_Water`** (`compiler_base.txt:1480`): the farthest token position
  ever consumed, deliberately *not* restored by `Rollback`. A failed parse can
  always report where it actually got stuck, independent of how far the
  backtracking unwound — the PEG equivalent of "farthest failure" error
  reporting.
- **Errors annotate tokens**: `Rollback` writes its reason onto the token at
  the failure point (`Top.Error = Error`), and successful consumption clears
  it. Diagnostics accumulate on the same element objects everything else uses.

### Packrat memoization with left recursion

`Parse_Memo` (`compiler_base.txt:1394`) implements packrat memoization plus
Warth-style left-recursion handling — needed once gal parsers began to be
*generated* from PEG grammars (the Python parser, chapter 10; both features
"live only in the gal3 generators").

One memo entry records the outcome of one rule at one token position. The
subtle part is that a gal parse rule doesn't return a value — it *pushes
element objects*; so the memo stores `Produced`, the list of element objects
the rule pushed, and a replay re-pushes **the same objects**, guaranteeing the
element tree is identical to a fresh parse (`compiler_base.txt:1501`).

Left recursion follows Warth et al.'s seed-growing, with a twist for
invalidation cost (all in `compiler_base.txt:1394–1596`):

- `Memo_Plant` inserts an `In_Progress` seed before trying a rule.
- A rule that re-enters its own seed fails that attempt (`Memo_Replay` returns
  false) and sets `Detected` — letting a non-recursive alternative produce the
  base case.
- The generated wrapper then *grows* the seed: reparse, and `Memo_Grew`
  accepts the new result only if it consumed strictly more tokens.
- **Invalidation is position-filtered**: while a seed is live, a `Recorder`
  collects the memo keys of entries settled *at the same start position* —
  "positions only move forward in a parse, so an entry at a later position can
  never consult a seed at an earlier one" (`compiler_base.txt:1549`). Each grow
  iteration invalidates only those, keeping regrowth near-linear.

### The element-order contract

The parser yields both the tree and a flat list, but the flat list is **not**
parse chronology. After parsing, `Derive_Elements`
(`compiler_base.txt:1964`) rebuilds it as a post-order walk of the tree:

```gal
comment `rebuild the flat element list as a post-order walk of the element
tree, so dependency order (children before parents) is a property of the
tree rather than of parse chronology. backtracking orphans and duplicate
token consumptions vanish because they are unreachable from the root.`;
```

Every element appears after all of its children (tokens as leaves). This is
the load-bearing contract of the whole inference pipeline (chapter 4):
bottom-up inferences walk the list forward, top-down inferences walk it in
reverse. It also launders backtracking — elements created by abandoned parse
attempts simply aren't reachable from the root and vanish from the list.
Memoization is unsound without this rebuild: replayed rules would otherwise
inject elements at the wrong chronological positions.

## Stage 2: classification

### Direction and dispatch

`Infer_Classification` (`compiler_base.txt:2014`) walks the flat list **in
reverse** — parents before children — asking each `Spell`'s dialect to
classify it:

```gal
for Index range End 0 -1
{
    Elem = (lget [my Elements] Index);
    if (Elem is a Spell)
    {
        try   { [Elem.Dialect].Classify Elem; }
        catch { D.Classify Elem; }
    }
}
```

(An element may carry its own dialect — this is how embedded dialects work;
otherwise the compiler's dialect applies.)

### Verb recognition: longest keyword subsequence

`Dialect.Classify` (`compiler_base.txt:1024`) first separates the element's
tokens into keywords (per the dialect's keyword dictionary) and words. Then
`Choose_Class` (`compiler_base.txt:906`) determines the element's **verb** —
the multi-word key identifying the construct:

- It generates the ordered combinations of the element's keywords
  (e.g. for `for range I 1 20` with keywords `for`, `range`: candidates
  `for`, `range`, `for range`) with their lengths.
- The **deepest candidate that exists in the dialect's dictionary** wins
  (`Statements`, `Operations`, or `Syntaxes` dictionary per shape). So
  `class set` beats `class`, `else if` beats `else`, `for range` beats `for`.
- The verb's keywords are then removed from the argument list, leaving the
  true arguments.

This is longest-match keyword dispatch over a *dictionary* — the dialect —
rather than over grammar productions. It's what makes gal's surface syntax so
plastic: any keyword sentence can become a construct by declaring its verb.

### Classification objects, not tags

The dialect dictionary maps a verb to a **prototype object** of the construct's
class (e.g. `If_Statement`, `For_Statement`, `Class_Append_Statement` — the
tree of ~40 statement classes at `compiler_base.txt:1088–1392`). Classification
instantiates a *fresh object* of that class and mirrors the parse element's
structure onto it:

```gal
method void Classify_As [object C]
{
    my Classification = C;
    for each E in [my Elements]   { push [C.Elements]  [E.Classification]; }
    for each E in [my Arguments]  { push [C.Arguments] [E.Classification]; }
    for each E in [my Listargs]   { push [C.Listargs]  [E.Classification]; }
    ...
}
```

Note what's being pushed: `[E.Classification]` — the classification of each
child, not the child itself. Since classification runs top-down (reverse
order) and children classify after parents... each parse element's
`Classification` property defaults to `[self]`
(`compiler_base.txt:32`), so unclassified children pass through as
themselves, and are later re-pointed when their own classification runs. The
result is **two parallel trees**: the parse tree (what the text looked like)
and the classification tree (what the program means), linked element-by-
element. All later inferences — type inference, variable registration, code
generation — run on classifications (`[Elem.Classification].Infer_Appends`,
`[E.Classification].Register_Variables`, etc.), while the parse elements
retain full source fidelity underneath.

Two per-token consequences documented in `gal3/CLAUDE.md` follow directly:
classifications are **per-token objects**, so name references resolve types
via `Get_Variable_Context().Variables` rather than via shared classification
state, and generators must dereference `[Arg.Classification]` to read
precedence.

### Failure is soft and observable

An element whose verb matches nothing self-classifies (`Elem.Classification =
Elem`) and the miss is counted in `Unclassified_Verbs`
(`compiler_base.txt:986`); `Print_Unclassified_Verbs` reports the tally after
compilation. An unknown construct doesn't kill the parse — it flows through
the pipeline as a generic element until something downstream needs it to mean
something. This tolerance is what "skycoding" (chapter 5) leans on.

## Conventional theory comparison

| aspect | conventional design | gal3 |
|---|---|---|
| grammar's role | grammar productions define the construct inventory; parse actions build typed AST nodes | grammar defines only 4–5 *shapes*; construct inventory is a runtime dictionary (the dialect) |
| adding a construct | edit grammar, regenerate parser, add AST node type | add a dialect declaration + element class; parser untouched |
| AST | single tree of construct-typed nodes; tokens/trivia usually discarded or in a side table | two linked trees: full-fidelity parse elements + construct-typed classification objects |
| keyword recognition | reserved words baked into the lexer/grammar | keywords are dialect data; verb = longest keyword subsequence found in a dictionary |
| error recovery | grammar-level recovery productions, panic mode | soft self-classification + unclassified-verb telemetry + high-water diagnostics |
| memoization | packrat (Ford), left recursion via Warth seed-growing | same algorithms, plus object-identity replay (`Produced`) and same-position invalidation filtering |

Framing points for the paper:

- **The nearest relatives are "parse, then disambiguate" architectures** —
  e.g. C compilers resolving the lexer hack, or IDEs' lossless syntax trees
  (Roslyn's red/green trees, rust-analyzer) that keep full fidelity and layer
  semantics on top. gal3 pushes further: *every* construct decision, not just
  ambiguous ones, is deferred to a post-parse, data-driven pass.
- **The shape grammar is closed; the language is open.** This inverts the
  usual extensibility trade-off. Macro systems (Lisp, Rust) achieve openness
  by staging *expansion*; gal3 achieves it by staging *interpretation of an
  intentionally underspecified parse*. Statements are effectively
  s-expressions delimited by `;` and `{}` instead of parentheses, with the
  head symbol found by dictionary lookup anywhere in the keyword sequence
  rather than fixed at position zero.
- **Classification-as-object is the hook for everything else.** Because the
  classification is an instance of a class in an open hierarchy, per-construct
  behavior for every later stage (lowering, type inference, five backends) is
  ordinary method dispatch — including methods grafted on by sideways
  inheritance (chapter 6). The dragon-book compiler dispatches on node *kind*
  in each pass's switch statement; gal3 dispatches on node *class* once, at
  classification time, and inherits that decision everywhere.
