# Dialects: the language as data

*Chapter 7 of the gal3 compiler design documentation. Sources:
`gal3/compiler_dialect.txt` (the compiler dialect, 1449 lines),
`gal3/fallback_inference.txt:1229–1382` (declaration lowering),
`gal3/gal_base.txt:49–99` (the shape grammar), `gal3/synthesis.txt`.*

## What a dialect is

> "A dialect is an object having a list of language elements. Each element is
> associated with one or more keyword combinations, and there are three
> element dictionaries: Statements, Operations and Syntaxes… There are no
> reserved words in gal… when you write gal code, you need to have a specific
> dialect in mind." — `gal3/synthesis.txt`

`compiler_dialect.txt` — the vocabulary the compiler itself is written in —
**contains no parsing code at all**. It is a sequence of `statement`,
`operation`, and `syntax` *declarations* (each producing one element class)
followed by one `dialect` block (registering verb strings to those classes).
The grammar in `gal_base.txt` is verb-agnostic; the dialect is what makes
`say`, `for range`, or `class set` mean anything.

## Anatomy of a declaration

A statement declaration (`compiler_dialect.txt:80`):

```gal
statement Property 'property' Property
{
    keyword Type 'type' 'string';
    argument Name 'property' 'variable';
    optional Value 'value' 'variant';
}
```

- `statement` … `Property` — generates `class Statement_Property`, with base
  class `Statement` (the `_Statement`-family prefix is itself declared: the
  meta-declaration `statement Statement 'statement' Class_Generator {...
  property string Base_Class 'Statement'; }` at `compiler_dialect.txt:25`
  makes the declaration statements *ordinary dialect statements too* — the
  mechanism describes itself).
- `'property'` — the canonical verb string.
- trailing `Property` — the parent class, mapped by suffix convention to the
  hand-written behavioral skeleton `Property_Statement` in
  `compiler_base.txt`. A declaration picks its runtime behavior *family* by
  naming a parent.
- `keyword` members are part of the verb (no argument position); `argument`
  members are required positional arguments; `optional` are optional. Each
  member carries a name, a type word, and a usage role — and the vocabulary
  deliberately mixes real types (`string`, `number`) with roles (`variable`,
  `value`, `class`, `method`); the real type names later drive usage stamping
  (chapter 10).

An operation declaration carries **precedence and result type as ordinary
property defaults** (`compiler_dialect.txt:264`):

```gal
operation Not_Equal '!=' Binary
{
    argument Op1 'variant' 'value';
    argument Op2 'variant' 'value';
    property integer Python_Precedence 11;
    property integer Javascript_Precedence 11;
    property string Data_Type 'flag';
}
```

Precedence numbers (call `.` = 2, `*` = 5, `+` = 6, comparisons = 11,
`not` = 12, `and` = 13, `or` = 14; lower binds tighter) and result types ride
the same channel — declaration property defaults materialize in the generated
`__init__`, so every *instance* of the operation is born knowing its
precedence and type without any handler.

Declarations can also carry **methods** — full behavior shipped inside the
declaration. `for range` (`compiler_dialect.txt:178`) embeds its own
`Register_Variables` declaring that "the loop variable of a counted range is
definitionally an integer." Declaration and implementation of a language
element are one artifact.

## How declarations become code

Nothing interprets declarations at parse time. When the dialect file is
*compiled*, one fallback generator (`generate Class_Generator_Statement`,
`fallback_inference.txt:1345`) turns each declaration into ordinary gal class
definitions that become part of the **next** compiler generation:

- `statement Foo 'foo' Line { ... }` → `class Statement_Foo is Line_Statement
  { property string Keyword 'foo'; ...members...; method number Attributes
  {...} }`.
- Each `argument` emits a `property object <Name>;` plus a snippet in the
  generated `Attributes` method that *positionally binds* parsed arguments:
  `my Name = (shift [my Listargs]);` with an arity error for missing required
  arguments, and stamps the declared type/usage onto the bound argument. This
  is the moment a generic parsed statement acquires named fields like
  `[my Condition]`.
- The `dialect Compiler { statements, ... }` block lowers to `class
  Dialect_Compiler is Dialect` whose generated `Initialize` registers a
  **prototype instance** per class into the three dictionaries and registers
  every word of every verb as a keyword:

```gal
statements,
    Statement_Add    '+' 'add' '+=' '+ =',
    Statement_Append 'append' 's+' 's +',
    Statement_Say    'say' 'print' 'console' 'write line',
    ...
```

Synonyms are free (`say`/`print`/`console`/`write line` all classify to
`Statement_Say`); multi-word verbs are ordinary (`'for each in'`,
`'is not a'`); punctuation variants tolerate tokenizer splitting (`'+ ='`).
One verb string can name a statement, an operation, *and* a syntax
simultaneously (`'.'` is `Statement_Call`, `Operation_Call`, and
`Syntax_Property`) — the surface shape selects the dictionary. Dialects can
inherit (`dialect X is Y` → `class Dialect_X is Y_Dialect`), and a compiler
selects its dialect by simple property assignment
(`C.Dialect = (new Dialect_Documentation)`).

This is the self-hosting trick at its sharpest: **the dialect is data to the
compiler compiling it, and code in the compiler that results.**

## Even the grammar is a declaration

The entire concrete grammar of gal is ~50 lines of `parser` declarations in
`gal_base.txt:49–99`:

```gal
parser Gal
{
    sequence Program    [repeating Statement];
    sequence Statement  [repeating Expression] [optrep Statement_Tail] Statement_End;
    either   Expression Operation Syntax Token_Number Token_Quote Token_Keyword Token_Word;
    either   Statement_End ";" Block;
    sequence Block      "{" [optrep Statement] "}";
    sequence Operation  '(' [repeating Expression] ')';
    sequence Syntax     '[' [repeating Expression] [optrep Syntax_Tail] ']';
    ...
}
```

No statement keyword appears anywhere in it — a Statement is "a run of
expressions, optional comma tails, then `;` or a block." The `parser` /
`sequence` / `either` constructs are themselves dialect statements whose
fallback generators emit a generated `Gal_Parser` class: each rule becomes a
packrat-memoized `Parse_<Rule>` method, and **grammar rule names are element
class names** — `sequence Statement` constructs `new Statement`, so the
grammar's output is directly the element tree of chapter 3. The same
machinery, fed `grammars/python-3.11.gram` instead, generates the Python
parser (chapter 11).

## Coverage-driven language development

Because the grammar is shape-generic, **a brand-new verb parses today, before
it exists** — it lands in the `Unclassified_Verbs` tally and gets reported,
not rejected. The development loop the architecture induces:

1. Write the program you wish you could write.
2. Compile; read the unclassified-verbs report (and the untyped-operations
   report from the type-inference side).
3. Add declarations + dialect entries + fallback lowerings until both reports
   are empty.

The house rule (`gal3/CLAUDE.md`): "Add a language feature by declaring it in
the dialect and giving it a fallback lowering; add per-target generators via
sideways inheritance in the backend files." A new construct usually needs
**zero backend work**: `Statement_Python_While` has no generator anywhere —
it lowers once, in gal, to `forever { break if (not cond); ... }`, and every
backend inherits it.

The dialect file's second stratum shows this scaling up: ~200 lines of
Python-semantics elements (`python while`, `py +`, `py fstr`, `py slice`, …)
added for the Python-ingestion work — "each carries python semantics and
lowers to gal atomics in the fallback generators, so only atomic constructs
ever need a new target-language backend."

## Conventional theory comparison

| aspect | conventional design | gal3 dialects |
|---|---|---|
| construct inventory | grammar productions; changing it = regenerate parser | dictionary entries; changing it = recompile the dialect (data → classes) |
| reserved words | fixed keyword set in the lexer | none; keywords are per-dialect data |
| operator precedence | grammar stratification or precedence-climbing tables in the parser | property defaults on declared operation classes, read at *generation* time |
| syntax extension | macros (token/AST substitution at expansion time), or language workbenches (MPS, Spoofax, Rascal) with external metagrammars | in-language declarations compiled into the next compiler generation; surface shape fixed, vocabulary open |
| multiple languages in one toolchain | separate front ends | dialects sharing one shape parser and one element hierarchy; selected per compiler instance |
| unknown constructs | syntax error | parse fine, self-classify, get counted — coverage-driven development |

Framing points for the paper:

- **Dialects occupy a deliberate middle between macros and grammars.** Macro
  systems rewrite trees but keep the reader inside the host language's
  reading rules; language workbenches allow arbitrary grammar but at the cost
  of external metatools. gal fixes the *shape* grammar forever (four
  delimiters and a semicolon) and opens everything else as data — closer to
  Lisp's "syntax is a library" than to yacc, but with keyword sentences
  instead of parenthesized heads, and with the library compiled into the
  compiler rather than expanded per call site.
- **Declaration properties as the universal side-channel.** Precedence,
  result type, and keyword text all travel the same way: ordinary property
  defaults on generated classes, readable by any inference or backend through
  the classification. There is no separate precedence table, type table, or
  keyword table to keep in sync — the declaration *is* all three tables.
- **No reserved words is a real semantic stance**, not a parser trick: the
  same program text can mean different things under different dialects, and
  the Documentation dialect (chapter 12) exploits exactly that — articles
  about gal are gal programs whose verbs (`chapter`, `bash expect`) exist
  only in their dialect.
