# Data-type inference: definitional type, contextual usage

*Chapter 10 of the gal3 compiler design documentation. Sources:
`gal3/data_type_inference.txt` (487 lines, in the zero stack),
`docs/data_type_inference.md`, `gal3/compiler_base.txt:1098–1268`
(variable registration), consumption sites in the backends.*

## Two properties, not one

Every element carries two inferred string properties
(`data_type_inference.txt:33`):

```gal
class set Element
{
    property string Data_Type '';
    property string Usage '';
}
```

- **`Data_Type` is definitional** — what the element *is*: a quote token is a
  string, an addition is a number, a variable is whatever its declaration
  says.
- **`Usage` is contextual** — what the surrounding element applies: every
  argument of a `say` is used as a string; the condition of an `if` is used
  as a flag.

The deliberate stance: **mismatch is not an error.** "When the two differ, a
strongly typed generator converts; gal itself does not enforce agreement, so
a mismatch is the generator's decision, not an error." gal is not adding a
type *checker* — it is adding exactly the information a typed backend needs
to make conversion and formatting decisions. The type vocabulary is the fixed
scalar/collection set `flag integer number string list dictionary object`,
plus `variant`, which imposes nothing.

The motivating example (`docs/data_type_inference.md`): for
`say Message ' ' Total;` where `Total` is an integer, the inference leaves
`Total` with `Data_Type integer, Usage string` — exactly what a C generator
needs to choose `%d`, and what Go needs for its printf verb.

## Scopes come first

Inference #11 (`Infer_Variables`) runs one forward pass of
`Register_Variables` before typing starts. Registration is per-class
behavior (chapter 4): a declaration's **verb names the type** (`integer X`
registers `X → integer` in the enclosing context); plural forms register
every listed name; `property` registers on the *owner class* so `[my X]`
resolves against the class; functions register their parameters by walking
their bracketed typed-argument syntaxes; and `for range` registers its loop
variable as integer — from a method embedded *in the dialect declaration
itself* (chapter 7). Lookup climbs the `Get_Variable_Context` chain:
parameters, then locals, then enclosing scopes.

## Declarative where possible, handlers where not

The design rule: result types and usages are **declared in the dialect**;
code exists only for what cannot be declared.

- **Result types** ride the declaration-property channel (chapter 7):
  `operation Not_Equal '!=' Binary { ... property string Data_Type 'flag'; }`
  — instances default to their result type via constructor defaults, no
  handler at all. A quote token is born typed
  (`property string Data_Type 'string'` on `Token_Quote` in the base).
- **Declared usage** closes the loop between declarations and instances.
  `Element.Declared_Usage` (`data_type_inference.txt:65`) looks up the
  element's own *declaration* in the class registry
  (`Statement_Class:Names`), walks the declaration's `argument`/`optional`
  members in order, filters their type words to real type names, and stamps
  each onto the corresponding actual argument's classification, positionally,
  first-writer-wins. The dialect declaration *is* the usage table.
- **Hand handlers** are few and small (`data_type_inference.txt:144–398`):
  `Token_Number` (integer unless the text contains `.`); `Token_Word`
  (resolve through the context chain: `Lookup_Variable [my Text]`);
  `Syntax_My` (read the owner class's registry); the variadic string-usage
  family (`say`, `comment`, `error`, `append` string-type their arguments);
  declarations stamping their names definitionally; `Operation_New` typing
  itself `object`.

Because the flat list is post-order, **one forward pass suffices**: operands
are typed before the operations containing them. Where a type is genuinely
computed, the computation records its decision on the element so enclosing
elements see it in the same pass — the canonical case being the Python `+`
lowering (chapter 5), which sets `my Data_Type` as it chooses between
`append` and numeric `+`.

## The no-conversion policy for unknowns

Only a **definite `string`** operand in a numeric context converts;
`variant`/unknown is left alone. This is the property that let the inference
land safely: it ran in every compile from day one while remaining
**behavior-neutral** — the self-hosting fixpoint stayed byte-exact — and only
then were consumers added. Conservative inference + fixpoint regression is
the project's standard pattern for introducing a cross-cutting analysis.

## What consumes it

One inference drives five type systems (chapter 8):

| consumer | Data_Type decides | Usage decides |
|---|---|---|
| Python | whether to wrap a string operand: `int(x)`/`float(x)` | which width (`Usage 'integer'` → `int`) |
| JavaScript | `Number(x)` (else `+` would silently concatenate) | — |
| Go | printf verb per argument (`%d`/`%s`/`%g`, `%v` catch-all); `galAtoi`/`galAtof` helpers | width |
| Java | `Integer.parseInt`/`Double.parseDouble` | width |
| C++ | `std::stoi`/`std::stod` | width |
| C | printf format chars; `atoi`/`atof` | width |

The slogan from the docs: *Data_Type chooses whether to convert; Usage
chooses the width.* Declared types also flow into typed declarations
(`Go_Type`: integer→`int`, …) and container element types are recovered by
sibling scan where inference stops at "dictionary" (chapter 8).

Like classification (unclassified-verbs report) and generation
(error-per-element), typing has a coverage instrument: `Data_Type_Report`
counts elements per type and per usage and lists **untyped operation
classes** — the same coverage-driven development loop. Verified by
`bin/typedemo_oracle.sh` (one program → Python, JS, C → byte-identical
output). Known gaps are recorded in `docs/status.md`: method return types at
call sites (needs a method registry), `[my A B]` chains, `iterate`/for-each
loop variables.

## Conventional theory comparison

| aspect | conventional design | gal3 |
|---|---|---|
| goal | soundness: reject ill-typed programs | information: give typed backends conversion/formatting decisions |
| mismatch | type error | a documented generator decision (insert conversion) |
| inference algorithm | unification / constraint solving (Hindley–Milner), bidirectional checking | single bottom-up pass over the post-order list + declared defaults + context stamping |
| flow direction | synthesized + inherited via judgments | `Data_Type` = synthesized attribute; `Usage` = inherited attribute — the attribute-grammar pair, by name |
| where types are declared | type annotations in the program | the program's declarations *and* the dialect's element declarations (result types, argument usages) |
| unknowns | type variables to be solved, or `any` | left empty; **no conversion is emitted** — gradual by omission, with fixpoint neutrality as the safety proof |
| soundness story | proven or tested type system | behavioral oracles on generated programs across targets |

Framing points for the paper:

- **This is the soft-typing / gradual-typing end of the spectrum, applied to
  translation rather than checking.** Like soft typing (Cartwright–Fagan),
  inference never rejects; unlike it, the payoff isn't optimization or early
  warnings but *cross-language fidelity* — `'42' + 8` must be 50 in every
  target, including the ones where `+` would silently concatenate.
- **Usage/Data_Type is inherited/synthesized attributes made explicit and
  stringly-simple.** No constraint solver, no lattice: a seven-name type
  vocabulary, positional stamping from declarations, and one pass. The bet is
  that for a translation pivot, *most* of the value of typing is in the easy
  90% — and the untyped-operations report plus the loud-failure backends
  catch the tail instead of a solver.
- **Behavior-neutral landing is methodologically notable**: a compiler with a
  byte-exact self-compilation fixpoint can introduce a new global analysis
  and *prove it changed nothing* before wiring any consumer — a regression
  discipline conventional compilers approximate with test suites.
