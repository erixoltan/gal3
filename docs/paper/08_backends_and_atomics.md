# Backends and the atomic-element contract

*Chapter 8 of the gal3 compiler design documentation. Sources:
`gal3/python_inference.txt` (reference backend), `javascript_inference.txt`,
`go_inference.txt`, `java_inference.txt`, `cpp_inference.txt`,
`c_inference.txt`, the `*_main.txt` drivers, `docs/five_languages.md`,
`gal3/bin/five_oracle.sh`.*

## A backend is a list of `generate` bodies

Because fallback lowering (chapter 5) removes every high-level abstraction
before a backend runs, a target-language backend is definitionally **the set
of generator bodies for the atomic element list** — nothing more. Each backend
is one `<lang>_inference.txt` + `<lang>_main.txt` pair, a 1:1 mirror of
`python_inference.txt`: same generate list, language-specific bodies. Every
backend file has the same four-part layout:

1. `class set Element` / `Spell` / `Statement` / … — sideways-grafted output
   properties (`Python`, `Go`, …), precedence properties, and helpers.
2. `generator <Lang> Fallback { generate <Class> ...; ... }` — the generate
   list: one generator per atomic element class.
3. `class <Lang>_Compiler is Fallback_Compiler` — whose `Infer_Code` drives
   the generation.
4. `<lang>_main.txt` — a ~22-line CLI driver.

## The atomic contract, measured

Counting `generate` statements per backend:

| backend | generators | notes |
|---|---|---|
| python | 145 (143 classes) | reference; self-hosting target |
| javascript | 142 | identical list to Python minus the Python-only `Statement_Shell_Capture` |
| go / java / c++ | 59 each | **exactly identical** lists — the five-programs coverage-contract subset |
| c | 34 | strict subset of the 59, minus classes and collections (frozen POC) |

The 143-class self-hosting list spans structural elements (`Program`,
`Block`, `Token`, `Token_Quote`, `Element` as catch-all), declarations,
OO (`Statement_Class`, `Statement_Method`, `Operation_New`, `Syntax_My`, …),
control flow, arithmetic/comparison/logic operations, a large string family,
collections, literal syntaxes (`Syntax_Line`/`Tab`/`True`/`Null`/…), I/O, and
ten `Operation_Python_*`/`Statement_Python_*` atoms that exist as targets of
the Python-ingestion chain (chapter 10). The 59-class subset backends add
three classes the full backends don't need: loud-failure defaults on the
abstract `Statement` and `Operation`, and typed scalar declarations
(`Statement_Integer`/`Number`/`Flag`/`Object`) because Go/Java/C++ must emit
declared types where Python/JS get by with the untyped
`Declaration_Statement`.

The contract is two-sided: fallback promises to lower everything *to* this
list; a backend promises to emit everything *on* it — and, by explicit design
rule, to **fail loudly beyond it** (`docs/five_languages.md`: "must handle
exactly this subset and fail loudly beyond it").

## `generate` is sugar for sideways inheritance

The generator syntax itself lowers (chapter 5) into `class set`
(`fallback_inference.txt:377–419`). This:

```gal
generator Python Fallback
{
    generate Statement_If
        "if " Condition (i Python_Block);
}
```

becomes literally:

```gal
class set Statement_If
{
    method flag Infer_Python
    {
        string Code "if " [my Condition Python] (i Python_Block);
        my Python = Code;
    }
}
```

So **a per-target generator is a method grafted onto the element class** —
backends are columns of sideways inheritance over one shared row of element
classes (chapter 6). Sugar details that make the one-liners terse: in the
expression form, each bare word (`Condition`) expands to
`[my Condition <Language>]` — "the target code of my Condition child" — and in
block form `i = Code;` lowers to `my <Language> = Code;`, with the property
name supplied by the enclosing `generator` statement. The `generator X
Fallback { ... }` wrapper also synthesizes the driver: a `<Lang>_Generator`
class whose `Infer_<Lang>` walks the flat post-order element list, dispatches
through each element's classification, copies results back to parse elements,
and records per-element errors. Post-order means children generate before
parents — `[my Condition Python]` is always already populated.

## One element, five languages

The mirror is literal. `Statement_Call`:

| target | body |
|---|---|
| Python | `Object '.' Method '(' (i Python_Args ', ') ')'` (+ runtime-import side effect) |
| JavaScript | `Object '.' Method '(' (i Javascript_Args ', ') ');'` |
| Go | `Object '.' Method '(' (i Go_Args ', ') ')'` |
| Java | `Object '.' Method '(' (i Java_Args ', ') ');'` |
| C++ | `Object '.' Method '(' (i Cpp_Args ', ') ');'` |

Same three property references, same shape, differing only in trailing `;`
and helper prefix. Where languages genuinely diverge, the divergence is
concentrated in exactly the generator that owns it:

- **`say`** — Python builds an f-string, JS a template literal, Go a
  `fmt.Printf` with a verb per *inferred type* (`%d`/`%s`/`%g`, `%v` as
  graceful catch-all; degenerating to `Println` when all-literal), Java a `+`
  concatenation with literal runs merged and a defensive leading `""` to
  force concatenation, C++ a `std::cout <<` chain with the newline folded
  into the trailing literal, C a `printf` with format chars from declared
  types. One abstract statement, six native idioms — all driven by the same
  shared inputs (`Data_Type`, `Unquoted`, argument lists).
- **`else` chains** — Go rejects a bare-line `else`, so the Go/Java/C++
  `Block` generators splice any statement beginning `else` onto the previous
  statement's closing brace. The divergence lives in `Block`, not in the
  else generators.
- **`Operation_New`** — `ClassName(args)` in Python, `new ClassName(args)`
  in JS/Java, a synthesized `NewClassName(args)` factory func in Go, and in
  C++ the *object declaration* re-slices the generated `ClassName(args)` to
  emit stack construction: `Account Acct("Ada Lovelace");`.
- **`for range`** — gal ranges are inclusive, so Python appends `+1` inside
  `range()`; the C-family targets emit `<=` loops; Java/C++ declare `int`
  because the shared inference registers the loop variable as integer.
- **classes** — Python synthesizes `__init__` from property defaults (via a
  `'{[(propinit)]}'` placeholder patched into constructor bodies); JS chains
  `super(...arguments)`; **Go has no inheritance**, so a class becomes a
  struct + `NewX` construction function + pointer-receiver top-level funcs,
  and the universal `Base` class vanishes; Java uses field initializers
  ("java field initializers run before the constructor body, so no default
  placement machinery is needed"); C++ emits in-class member initializers
  with objects as stack values.

## Cross-cutting mechanisms

**Imports — two architectures.** Python/JS use a per-module registry:
`Module_Statement.Add_Include` dedups include lines
(`compiler_base.txt:1381`), generators reach their module via
`Get_Module` parent-walking, and the module generator emits the collected
imports (a generated program imports only what it uses — e.g.
`from Runtime import Runtime` appears only when a call goes through the
runtime). Go/Java/C++ instead use **class-level registries on `Element`**
(`Go_Imports`/`Go_Helpers` + dedup sets) because "classes live outside the
module in gal"; the `Program` generator exploits post-order — statements
generate first, so the registries are complete when the header is assembled —
emitting `package main`, the import block, helper functions, then the body.
Java wraps helpers in a package-private `class Gal`; C++ needs no helpers at
all ("every conversion c++ requires is an expression").

**Type mapping.** Each typed backend has an explicit table ending in a loud
error (`Go_Type`: integer→`int`, number→`float64`, string→`string`,
flag→`bool`, else `error`); Java adds a boxed-type table for generic
positions. Container element types are inferred by **sibling scan**: gal's
inference stops at "dictionary", so the declaration reads the value type from
the first sibling `d=` assignment it can see — yielding `map[string]VT{}`,
`HashMap<String, VT>`, `std::map<std::string, VT>`. String-into-numeric
conversion (chapter on typing) is per-target:
`int()`/`Number()`/`galAtoi` helper (because `strconv.Atoi` returns two
values and can't sit in an expression)/`Integer.parseInt`/`std::stoi`.

**The escaping/f-string family.** The hardest-won backend code
(`python_inference.txt:108–221`):

- **Flatten first**: a nested `Operation_Append` inlines its segments into
  the parent's list (`Python_Append_Flatten`) — embedding a finished f-string
  inside another f-string's braces would nest same-quote f-strings, a
  pre-3.12 SyntaxError.
- **Escape per literal segment**: literal segments are escaped individually
  (`\`, tab, LF, CR; braces doubled only when embedding); embedded expression
  segments are *code* and pass through verbatim; the final quote wrap
  (`Python_Choose_Quotes`, trying `'`, `"`, `'''`, `"""`) must not re-escape
  the assembled body. The historical comment records the failure mode: "the
  old form re-enquoted everything, so each nesting level added an escape
  layer."
- JS escapes the template-literal metacharacters (`` ` ``, `${`); Go doubles
  `%` in format strings; Java/C++ avoid interpolation entirely by
  concatenating.
- **The `Unquoted` contract**: every backend's `Syntax_Line`/`Tab`/`Indent`/
  `Return` generator sets `my Unquoted` to the *real* control character as a
  side effect — gal string literals never process escapes, so this is the
  only channel through which format/comment builders get real newlines.

**Precedence at generation time.** The precedence table lives in the
*dialect declarations* (`operation Add '+' Binary { property integer
Python_Precedence 6; ... }`) — not in class-set defaults, which are silently
dropped on generated-only classes. Generators dereference
`[Arg.Classification]` to read it ("an argument captured during top-down
classification is still the parse element, so the classification must be
dereferenced"). `Python_Infix` parenthesizes the left operand at *greater*
precedence and the right operand at *greater-or-equal* — "infix operators
associate left: 10 - (4 - 3)". N-ary chains parenthesize every non-first
operand at equal precedence. The subset backends sidestep the table entirely:
every binary operation is unconditionally parenthesized, and chains longer
than two operands are an explicit error — correct-by-construction over
pretty.

**Indentation.** Python/JS have quote-state-tracking indenters (Python's
handles triple quotes); Go/Java/C++/C reuse the base `Element.Indent`, whose
quote table pairs typographic quotes — which is why every backend's comment
generator replaces quote openers in comment text with *closing homoglyphs*
(`'`→`’`) so they can't poison downstream quote tracking. Generated Go is
additionally `gofmt`-ed by the oracle.

## Failing loudly: a graded discipline

1. **Category defaults** (subset backends): `generate Statement { error 'no
   go generator for statement ' [class name]; }` — anything unimplemented
   dies with its class name. `generate Element { i = ''; }` keeps inert
   leaves silent.
2. **Explicit cliff-edge errors**: chains > 2 operands, repeated literals,
   `main` with arguments, un-inferable dictionary value types, untyped
   parameters ("objects are stack values in c++, passing them is outside the
   contract"), untyped assignment in C++ ("might be an object alias, which
   would silently copy").
3. **`else { debug; }` tripwires** (self-hosting backends): an unrecognized
   class-body statement kind drops into the debugger mid-generation — the
   documented extension point for new statement kinds.
4. **Argument guards**: a child that failed to generate cannot silently
   vanish from an argument list (`error 'Argument Go not defined: ' ...`).
5. **Driver-level propagation**: the newer drivers fail the compile if any
   element's generator errored ("a generator error on any element must fail
   the compile, not leak None into the output") — the C driver still has the
   older silent-continue hole, noted for repair.

The behavioral check on all of this is `bin/five_oracle.sh`: five programs ×
five languages, each cell running the real pipeline (`gal → fallback ×2 →
gal<lang>` → native compile with `-Werror`-grade flags → run), requiring
**byte-identical program output** across all targets — 26 green cells.

## The drivers

Each `*_main.txt` is the same ~22-line shape: instantiate `<Lang>_Compiler`,
run the full `Infer` pipeline, write the generated code, and write an
`.elems` element-tree report (always in Python/JS; on failure only in the
newer drivers). The per-backend `Infer_Code` runs `Infer_Gal` and
`Infer_Fallback` first — every element gets its gal and lowered-gal
properties before target generation — then the synthesized `Infer_<Lang>`,
then verifies the root `Program` element actually has code.

## Conventional theory comparison

| aspect | conventional design | gal3 |
|---|---|---|
| retargeting interface | a fixed IR (LLVM IR, RTL, JVM bytecode) + instruction selection per target | a fixed *set of atomic source-level elements* + one string-building generator method per element per target |
| where language idioms live | lowering passes per target in the middle end | entirely inside the per-element generator bodies (f-string vs printf vs `<<` chain) |
| backend correctness | ISel/regalloc verified by test suites; formal semantics rare | byte-identical cross-target output oracle + loud-failure discipline + `-Werror`-clean native compiles |
| output level | machine/bytecode | idiomatic human-readable source (a transpiler family, not a code generator) |
| adding a target | new ISel, ABI, runtime port — months | mirror the reference file's 59-item generate list — Go, Java, and C++ each landed in ~a day (2026-07-11/12) |
| coverage policy | total (must compile everything) | explicitly partial with loud edges — "handle exactly the contract subset and fail loudly beyond it rather than emitting subtly wrong code" |

Framing points for the paper:

- **The "IR" is high-level and syntax-shaped.** Conventional wisdom lowers to
  a small orthogonal instruction set; gal3 lowers to a small orthogonal
  *statement* set that is still recognizably structured source. This is what
  makes emitting *idiomatic* target code tractable — the generator for `say`
  can still see "this is a print of these typed arguments," information a
  three-address IR would have destroyed. The cost: atomics must be chosen so
  that all targets can express them idiomatically, and genuinely
  target-hostile abstractions (inheritance in Go, aliasing in C++) surface as
  contract edges rather than being compiled through.
- **Partial-by-design backends invert the usual completeness norm.** The
  59-element contract + loud failure is a deliberate engineering stance:
  correctness of the covered square, plus honest refusal outside it, beats a
  total backend that is subtly wrong in the tail. The oracle then makes the
  covered square behaviorally exact.
- **The mirror structure is the readability payoff of the whole
  architecture**: because fallback removed abstraction and sideways
  inheritance packages per-target behavior, the five backends can be read
  side-by-side as parallel translations of the same 59 sentences — which is
  precisely the artifact the five-languages article exhibits.
