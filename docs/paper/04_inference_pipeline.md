# Compilation as a sequence of inferences

*Chapter 4 of the gal3 compiler design documentation. Sources:
`gal3/compiler_base.txt` lines 1647–2234 (`Compiler`, `Infer_Input`,
`Infer_Output`), `attributes_inference.txt`, `structure_inference.txt`,
`data_type_inference.txt`, `llm_inference.txt`.*

## The organizing idea

gal3 does not have "phases" that transform one representation into another
(text → tokens → AST → IR → code). It has **one growing population of element
objects** and a fixed sequence of **inferences** that each add information to
that population. An inference never replaces the representation; it enriches
it. The `Compiler` object itself is a `Document` — an `Element` — so the
compiler, the program, and every character of its text live in the same class
hierarchy.

The driver (`Compiler.Infer`, `compiler_base.txt:1665`) runs two banks:

**`Infer_Input` — the front end** (`compiler_base.txt:1689`):

| # | inference | adds |
|---|-----------|------|
| 1 | `Infer_Text` | the source text (from file) |
| 2 | `Infer_Characters` | one `Character` object per char, linked `Prev`/`Next` |
| 3 | `Infer_Tokens` | `Token` objects that absorbed those characters |
| 4 | `Infer_Elements` | the parse-element tree + the flat post-order list |
| 5 | `Infer_Components` | each element's `Arguments`/`Listargs`/`Block`/`Statements` |
| 6 | `Infer_Classification` | the parallel classification tree (chapter 3) |
| 7 | `Infer_Attributes` | per-construct attributes (names, types, variables) |
| 8 | `Infer_Appends` | cross-element relationships; records `class set` targets |
| 9 | `Infer_Ordering` | executes sideways inheritance splices; re-derives order |
| 10 | `Infer_Structure` | owner/parent hierarchy |

**`Infer_Output` — the back end** (`compiler_base.txt:1817`):

| # | inference | adds |
|---|-----------|------|
| 11 | `Infer_Variables` | scope dictionaries: every declaration registers name→type |
| 12 | `Infer_Type` | data types on every element (chapter on typing) |
| 13 | `Infer_Class_Structure` | class hierarchy relationships (currently `todo`) |
| 14 | `Infer_Inheritance` | inheritance rules for class-less targets (currently `todo`) |
| 15 | `Infer_Code` | the generated output text (`Gal`, `Python`, … properties) |
| 16 | `Infer_Intelligence` | reserved LLM hook (currently disabled) |

Each step is checked (`if (Result = 0) { say "Failed at ..."; return 0; }`)
and, in debug mode, followed by an `Element_Report` diff — the driver prints
the element tree again *only if an inference changed it*, which makes the
pipeline's effect on the representation directly observable
(`compiler_base.txt:1726–1812`).

## Dispatch: every element class answers every inference its own way

An inference is a *broadcast*: the compiler loops the flat element list and
invokes the inference method on each element (or on its classification):

```gal
method number Infer_Components
{
    for each Elem in [my Elements] { Elem.Infer_Components; }
    return 1;
}

method number Infer_Appends
{
    for each Elem in [my Elements]
    {
        Classification = [Elem.Classification];
        continue if (Classification.Infer_Appends);
        ...
    }
}
```

The per-element behavior lives in the element **class hierarchy**, not in the
pass. `Element.Infer_Appends` defaults to "nothing to do" (`return 1`,
`compiler_base.txt:138`); `Class_Append_Statement.Infer_Appends` overrides it
to locate its target class and queue the splice (`compiler_base.txt:1295`).
`Token.Infer_Gal` returns its own text; `Program.Infer_Gal` concatenates its
statements' `Gal`. A new construct participates in every pipeline stage by
overriding exactly the methods where its behavior differs from its
superclass — usually one or two.

This is the inversion that defines the architecture: **in a conventional
compiler, a pass owns a switch over node kinds; in gal3, a node class owns a
method per inference.** Adding a construct touches one class (plus a dialect
declaration); adding an inference touches one method name across the classes
that care. Combined with sideways inheritance (chapter 6), even those methods
can be contributed from separate files, so neither axis of the expression
problem forces edits to existing code.

The pipeline even has surface syntax for this shape: an inference file is
written as `inference Attributes { handle Statement_Class { ... } ... }`,
and each `handle C { body }` lowers (chapter 5) to `class set C { method
flag Infer_Attributes { body } }` — a named, distributed method installed
sideways across the element classes. `attributes_inference.txt`,
`structure_inference.txt`, and `data_type_inference.txt` are each one such
distributed method plus a `handle Compiler` driver loop.

Two of the input-bank inferences deserve a concrete word:

- **Attributes (#7)** runs each classification's *generated* `Attributes`
  binder (the positional shift of parsed arguments into named properties,
  chapter 7) followed by its `Infer_Attributes` handler. Its main handlers
  build the **global class registry** `Statement_Class:Names` — every class
  defined in the program, including the synthesized `Statement_*`/
  `Operation_*`/`Syntax_*` names of dialect declarations — the registry that
  `class set` splicing and declared-usage stamping later consult.
- **Structure (#10)** walks in reverse building the ownership tree: parents
  set `Elem.Parent` on their arguments and block statements, propagate the
  dialect, and chain siblings — `Next_Element`, overridden by `If_Statement`
  to record `Next_Else` and by `Try_Statement` to record `Next_Catch`, which
  is how `else` and `catch` attach to their governing statements *without
  grammar support*.

## The element-order contract

Inferences never walk the tree recursively; they iterate the **flat list**,
whose post-order derivation (chapter 3) makes direction meaningful:

- **Forward = bottom-up.** Children precede parents, so a forward walk sees
  every child's inferred properties before the parent computes its own.
  Components, appends, and type inference run forward — e.g. an operation's
  data type can read its operands' already-inferred types in a single pass.
- **Reverse = top-down.** A reverse walk sees the parent first — so owners can
  tell children who owns them before the children propagate further down.
  Classification and structure run in reverse.

A single sorted list serving both directions is the pipeline's key economy: no
inference needs its own traversal logic, and *order-sensitivity is reduced to
a one-bit choice per inference*. The contract must be re-established whenever
the tree is rearranged — which is why `Infer_Ordering` re-runs
`Derive_Elements` after splicing `class set` blocks (`compiler_base.txt:2090`),
so appended methods precede their class in dependency order and single-pass
bottom-up inference stays correct.

## Scope and variables as element behavior

Even symbol tables follow the dispatch pattern. There is no global symbol
table object; scope is a *chain of elements that claim to be variable
contexts*:

- `Element.Get_Variable_Context` (`compiler_base.txt:150`) asks its
  classification, then its parent — "an element does not know, so it asks its
  parent; elements that act as a variable context, such as methods, return
  themselves."
- `Function_Statement` and `Module_Statement` return `[self]` and carry
  `Variables`/`Parameters` dictionaries (`compiler_base.txt:1177`, `1360`).
- `Infer_Variables` (#11) broadcasts `Register_Variables`: each declaration
  class knows how to register itself. `Declaration_Statement` derives its type
  from its own verb (`integer X` declares an integer,
  `compiler_base.txt:1098`); `Property_Statement` registers against the
  *owner class* rather than the method scope; `Function_Statement` walks its
  own parameter syntaxes.
- Lookup (`Lookup_Variable`) climbs the same chain: parameters, then locals,
  then enclosing contexts.

Scoping rules are thus distributed across the classes that define scopes —
consistent with everything else in the compiler.

## Failure posture

Two idioms recur throughout the pipeline and are part of its design:

- **`forgive { ... }`** — try, and silently accept absence. Much of inference
  is "add this fact if the ingredients exist"; forgiveness makes every
  inference total over the heterogeneous element population without
  kind-checking boilerplate.
- **`debug;`** — unrecognized cases in otherwise-exhaustive dispatch (e.g. the
  `else { debug; }` arms in backend generators) drop into the debugger rather
  than emitting wrong output. The design rule is *fail loudly at the exact
  element*, in the target-language debugger, with the whole element tree live
  for inspection.

## The reserved seam: `Infer_Intelligence`

Inference #16 and the `llm_inference.txt` layer reserve a pipeline position
for LLM-assisted inference — lowering a skycoded element, proposing a data
type, generating an idiom no rule handles. It is currently commented out of
the driver (`compiler_base.txt:1894`); the compiler self-hosts on rule-based
inference alone. Architecturally the point is that an LLM would be *just
another inference* over the same element population, with the same per-class
dispatch — see `docs/inference_process.txt` for the intended methodology
(probe → LLM-infer → human-proof → capture as test → replace with fast code).

## Conventional theory comparison

| aspect | conventional design | gal3 |
|---|---|---|
| unit of organization | passes over successive IRs (AST → typed AST → IR → …) | inferences over one persistent element population |
| per-construct behavior | switch/visitor in each pass | method per inference on the element class |
| traversal | each pass implements its own tree walk | shared flat post-order list; forward=bottom-up, reverse=top-down |
| symbol tables | dedicated symbol-table structures per scope kind | scope = elements that answer `Get_Variable_Context`; registration is broadcast dispatch |
| adding a construct | touch every pass's switch | one class + dialect entry; methods may arrive via `class set` |
| adding an analysis | new pass with new traversal | new `Infer_*` broadcast + overrides where behavior differs |
| information flow | dataflow between IRs, often lossy | strictly accretive; text/positions never discarded |

Framing points for the paper:

- **Closest formal relative: attribute grammars.** Forward-walk inferences
  compute synthesized attributes; reverse-walk inferences compute inherited
  ones; the post-order list is a topological order that makes one evaluation
  pass per inference sufficient. But gal3's "attributes" are computed by
  arbitrary methods on an open class hierarchy rather than by equations
  attached to grammar productions — attribute grammars with late-bound,
  inheritance-shared, externally extensible rules.
- **Contrast with nanopass.** Nanopass compilers (Sarkar/Waddell/Dybvig) also
  favor many small passes, but each pass maps between two *closed,
  formally-declared IR languages*. gal3 keeps one open representation
  throughout and lets each inference be partial (via `forgive`) rather than
  total by construction. The trade: nanopass gets per-pass machine-checked
  invariants; gal3 gets an open construct inventory and total uniformity.
- **The visitor pattern is dissolved, not implemented.** Visitors exist to add
  operations to a fixed node hierarchy without editing it. gal3 instead makes
  the hierarchy editable from a distance (sideways inheritance), so operations
  are plain methods and both axes of the expression problem stay open — at the
  cost of static checkability, which the fixpoint build and oracles (chapter
  9) reintroduce empirically.
