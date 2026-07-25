# Parsing PEG and Python with gal — Design Document

**Status:** Draft for review
**Date:** 2026-06-16
**Context:** gal3 reached its 3.0.0 self-hosting fixpoint on 2026-06-10. This document captures the design for the next initiative: using gal's parser/generator machinery to parse external languages — starting with PEG grammar files and Python source — as the first concrete step toward gal serving as a universal translator.

---

## 1. Vision

gal — *general abstract language* — is intended to serve, eventually, as a universal translator: parse a program in any source language into gal **language elements**, then generate those elements back into a valid program in any target language. The element tree is the pivot.

The near-term goal of this initiative:

1. Parse **any Python program** into gal language elements.
2. Define a **language element class for every Python language construct**.
3. Define **generator rules** that regenerate those elements into a valid, *normalized* Python program.

The same elements could later be generated into C (a separate project). This document is about the framework that makes that possible, not about Python alone.

This design is the result of long iteration (the concept dates to 1987); it deliberately steps around two well-known traps — the universal-IR ("UNCOL") fantasy and byte-exact round-trip fidelity — both discussed below.

## 2. Goals and Non-Goals

**Goals**
- A robust, reusable **parser strategy**: one parsing engine, many grammars, driven by grammar description files.
- A robust, reusable **generator strategy**: per-language, per-target generation as open class extensions.
- Parse PEG grammar files (initiative 1) and Python source (the larger goal).
- Regenerate **normalized** Python (see §6).

**Non-Goals (for now)**
- A single universal intermediate representation that all languages share. We use a *faithful per-language element tree* instead (see §3.4).
- Byte-identical round-trip. We target normalized regeneration (see §6).
- Cross-language generation (Python → C). Separate project; the architecture allows it but it is irreducibly hand-authored per target.
- Error recovery / parsing invalid programs. Assume well-formed input.
- Performance tuning. The object-oriented overhead in gal is intentional — language element classes are a domain where inheritance genuinely pays, and translating Python faithfully into another target is closer to AI than to compilation. All that is required is that performance *scales* to larger programs (memoization, §5 Tier 1, is a scaling requirement — exponential → linear — not a speed optimization). Once a Python program is converted to gal syntax with Python-specific elements, the existing gal compiler carries the subsequent translation steps, and its performance is adequate.

## 3. Architecture

### 3.1 Two distinct kinds of parser — keep them separate

A frequent source of confusion is that "parser" means two different things in this system, at two different layers:

- **Metagrammar parsers** read a *grammar description file* and run **once, at build time**. These are `Peg_Parser`, `Bnf_Parser`, and any future siblings (`Ebnf_Parser`, `Antlr_Parser`, …). They are subclasses of `Parser` (`compiler_base.txt`).
- **Object-language parsers** read *programs* and run every time something is translated. `Python_Parser`, `C_Parser`, etc. These are **generated**, not hand-written.

`Peg_Parser` and `Python_Parser` both extend `Parser`, but they occupy different roles: the first consumes grammars, the second consumes programs.

### 3.2 The linchpin: a normalized Grammar IR

Every metagrammar parser must produce the **same normalized Grammar IR** — a small canonical model of grammar rules:

- `Rule` (named nonterminal definition)
- `Choice` (ordered alternation)
- `Sequence`
- `Repeat` (one-or-more / zero-or-more)
- `Optional`
- `Lookahead` (positive / negative)
- `Terminal` (literal / token class)
- `NonTerminal` (rule reference)

PEG `|` and BNF alternation both lower to `Choice`; PEG `e*` and EBNF `{ e }` both lower to `Repeat`. Downstream of the Grammar IR, **nothing cares which metalanguage the grammar came from.** One generator (Grammar IR → gal parser DSL) serves all input metalanguages. `Peg_Parser` vs `Bnf_Parser` differ *only* in front-end syntax.

### 3.3 The pipeline

```
grammar file (e.g. python.gram)
   │  Peg_Parser  (a Parser subclass — itself GENERATED from `parser Peg`)
   ▼
Grammar IR   (normalized: Rule / Choice / Sequence / Repeat / …)
   │  Grammar→gal generator   (emits `parser Python {…}` + one element class per rule)
   ▼
gal source  ──(existing gal compiler)──►  Python_Parser  +  Python element classes
   │  Python_Parser
   ▼
Python program  ───►  Python language elements   (tree of typed Element objects)
   │  Python_Generator   →  normalized Python source   (round-trip)
   └  C_Generator        →  C source                   (separate project)
```

The key property: **almost no parser is hand-written.** `parser Peg`, `parser Bnf`, and `parser Python` are all just grammars fed through the one generator. The only hand-written parser in the entire system is the gal bootstrap that already exists (`parser Gal_Token` and `parser Gal` in `gal_base.txt`). This initiative generalizes gal's *own* self-hosting bootstrap into a language-agnostic front-end/back-end framework. The uniformity is the robustness: one engine to harden, and every language inherits each fix.

### 3.4 No universal IR — and why that is correct

The dream of one intermediate language that all source languages funnel through (UNCOL, 1958) does not work: such an IR either grows without bound or collapses to a lowest common denominator. Every system that actually works (tree-sitter, Roslyn, LibCST) uses a **faithful per-language tree plus transformation rules between languages.** Our "element class per Python construct" *is* that — a Python-specific tree, not a god-IR. Consequence for cost:

- **Same-language normalized regeneration (Python → elements → Python) is cheap** — structural, driven by the grammar.
- **Cross-language generation (Python → C) is expensive** — irreducible semantic work, hand-authored per element per target pair. This is why C is a separate project.

### 3.5 Element classes: structure generated, behavior layered

In gal's parser DSL the **rule name is the element class** — the sequence generator emits `(new RuleName)` (see `Statement_Sequence` in `fallback_inference.txt`). So the Grammar→gal generator emits one element class per rule for free (`class Python_Funcdef is Element;`). Generation behavior is then attached with open classes:

```
class set Python_Funcdef { generate ... }
```

Structure comes from the grammar; behavior (how an element regenerates to Python, or later to C) is layered on via `class set` / `handle` extensions. This matches gal's existing mechanism exactly.

### 3.6 Python Specific Language Elements

gal has a 'say' statement class Statement_Say that can be generated into a python 'print' command. When parsing Python, we do not parse a 'print' function into a 'say' statement. Instead, we may have a Python-specific statement class 'Statement_Python_Print' if we feel it should be mapped to a statement, or we may even have a 'Python_Function_Print' class if we feel that the gal 'Statement' class is not a good match for Python functions that don't return a value, and we don't want to use gal 'Operation' classes because they always return a value and they are not exactly the same thing. 

The important decision is that we don't try to parse Python language elements into the existing gal language elements. Even the Python '-' operation shouldn't parse into the gal Operation_Minus but should instead by something Python specific. If we want to establish an equivalency between them, then the fallback generator logic can be used to create that equivalency. 

### 3.7 The element-order contract — what the parser owes the inference engine

The parser's output is not just a tree. It is **two coupled structures**, and the entire inference system is built on both:

1. **The tree** — every parent element knows its children (`copy [Element.Elements] = My_Elements` in the sequence generator).
2. **The flat list** — `Parser.Elements` holds *every* element in the program (tokens included, as leaves) in **dependency order**: every element appears after all of its children. This is post-order.

The inference engine consumes the flat list in both directions:

- **Bottom-up inferences** (`Infer_Python`, `Infer_Components`, `Infer_Appends`, …) iterate **forward**. Because children precede parents, a statement can rely on all its children having already defined their inferred properties (e.g. `Python`) when its own turn comes.
- **Top-down inferences** (`Infer_Structure`, `Infer_Classification`, …) iterate in **reverse** (`for Index range End 0 -1` in `compiler_base.txt`). Parents run before children, so a class can tell its members who their owner class is before those members propagate the information further down.

`Python_Parser` and every other generated parser **must honor this contract**, because all Python element behavior — regeneration, and eventually cross-language equivalence — will be written as inferences against it.

**Why the current mechanism cannot survive PEG backtracking.** Today the flat list is built *chronologically*: `Consume_Token` and `Add_Element` push onto `Parser.Elements` as the parse proceeds, and a sequence's parent element is created only after its children succeed. For a nearly deterministic grammar like gal's — where failed alternatives die on their first token, before creating any element — chronological order *is* post-order. But `Rollback` resets only `Char_Pos`/`Token_Pos`; it never retracts elements already pushed. Python's PEG grammar backtracks heavily *after* successful sub-parses, so failed alternatives would leave **orphan elements** in the flat list and inferences would run on parse attempts that lost. Memoization replay and left-recursion seed-growing (§5 Tier 1) sever the chronology↔post-order equivalence completely.

**Decision: derive the flat list; do not accumulate it.** After `Parse_Program` succeeds, build `Parser.Elements` by a single post-order walk of the tree from the root. Consequences:

- Orphans from failed alternatives simply are not reachable from the root — they vanish.
- Memoization only needs to cache (success, elements produced, ending position) per (rule, token position); replay re-links the same objects into the winning tree, and the final walk establishes order. Ordering stops being memoization's problem.
- Left-recursion seed-growing creates and discards partial trees freely; only the final tree is walked.
- The contract becomes a *defined property of the tree* rather than an accident of parse history — a strictly stronger invariant.

This change lands in the `Parser` base class and is validated by the self-hosting oracle (§5): for gal's own grammar the walk must reproduce today's chronological order, so the 3.0.0 fixpoint must still hold byte-exact. Do this **before or together with memoization**, since memoization is unsound without it.

**Synthetic rules must be inference-transparent.** Rule-lifting (§4) inserts hoisted elements (`Python_Expr__Group1`) between a Python construct and its real children, and those elements sit in the flat list and participate in *both* inference directions. They must be pass-through by default: derive every synthetic class from one shared base (`Python_Synthetic is Element`) whose default inferences forward top-down information (owner class, structure) to children unchanged and expose bottom-up results (generated text) upward unchanged. Hand-written per-construct inferences then target only the real, grammar-named element classes.

**Bonus: the same mechanism repairs sideways inheritance.** gal's `class set` / `class append` confounds the current chronological ordering: statements defined *after* a class textually become members of that class, so when the class's bottom-up inference runs, its appended members have not yet inferred — today this is absorbed by extra fallback/atomic iterations (the appended statement's inferred text is unavailable, so the generator falls back to raw gal source and a *second pass* cleans it up; see the `try { [Stmt.Fallback] } catch { [Stmt.Gal] }` in the fallback `Statement_Class` generator). With a derived element list the fix is structural: **execute** sideways inheritance — splice the `class set` block's statements into the primary class's element as real children — then re-derive the flat list by tree walk. The spliced members now precede their class in dependency order, single-pass inference becomes sufficient, and the same `Derive_Elements` walk serves both the gal compiler and every generated (PEG-based) parser. The natural pipeline slot is `Infer_Ordering`, which sits between `Infer_Appends` (which resolves class-set targets) and `Infer_Structure`, and is currently a stub.

## 4. PEG ↔ gal parser DSL mapping

gal's parser DSL is already a PEG engine: `either` lowers to ordered choice (`return [true] if (i Parse_X …)` in order — first match wins, PEG semantics, not ambiguous CFG alternation), and `sequence` rolls the whole rule back on any failed item. The mapping is nearly 1:1:

| PEG / Python grammar | gal parser DSL |
|---|---|
| `A \| B \| C` (ordered choice) | `either A B C` |
| `A B C` (sequence) | `sequence` with arguments |
| `e?` / `[ e ]` | `[optional e]` |
| `e*` | `[optrep e]` |
| `e+` | `[repeating e]` |
| `'literal'` | quoted token literal |
| `!e` (negative lookahead) | `[exclude e]` *(path still unproven — see §5)* |
| `&e` (positive lookahead) | **no direct equivalent** — compose or add |

Worked example already in the tree (`gal_base.txt`): `parser Gal_Token` is the lexer and `parser Gal` is the gal grammar, both written in this DSL and self-hosted to a fixpoint. A short standalone example is in `examples/parser_example.txt`.

**Rule-lifting.** gal requires a *named* rule for every nonterminal; `either`/`sequence`/`optional`/etc. target a single rule name or literal. PEG allows arbitrary inline nesting (`(a | b)+`, `[a b c]`). So the Grammar→gal generator's core transform — beyond the 1:1 table — is **hoisting every nested group/alternation/repetition into a synthetic named rule.** (Alternatively, inline grouping could be added to the DSL itself; see §5.)

## 5. Parser engine evolution

Today's engine is deliberately simple. The `Parser` base class (`compiler_base.txt`) provides token-stream navigation and backtracking only: `Top_Token`, `Parse_Token`, `Rollback`, `Consume_Token`, `Add_Element`, over a flat token list with `Char_Pos` / `Token_Pos`. Parsing a grammar *file* needs little more than this. Parsing real Python source needs the following.

**Strategic note — a built-in regression oracle.** Most of these changes live in the `Parser` base class and the sequence/either generators, *not* in language-specific code. That means each change can be validated against gal's own grammar (`parser Gal`) by confirming gal still self-hosts to the 3.0.0 fixpoint. Harden the engine with a byte-exact pass/fail test in hand, before Python is in the picture.

### Tier 1 — blocks Python at all
0. **Derived element list (§3.7).** Replace chronological accumulation of `Parser.Elements` with a post-order walk of the finished tree, so the dependency-order contract survives backtracking, memoization, and left recursion. Prerequisite for everything below; validated by the self-hosting fixpoint. **Do this first.**

   **STATUS: DONE (2026-07-03).** `Derive_Elements` / `Walk_Element` in `compiler_base.txt` (walk stops at tokens, whose `Elements` hold lexed characters). Verified: for gal's own grammar the derived list is exactly identical to the chronological list (17,041 elements, zero orphans, zero duplicates), and the five-artifact fixpoint holds. Sideways-inheritance execution (§3.7 bonus) is also done: `Infer_Ordering` splices class-set statement parse elements into the primary class and re-derives, so appended members precede their class in dependency order — single-pass inference now correct, confirmed by the first fallback pass emitting fully merged classes.
1. **Memoization (packrat).** Today every failed alternative re-parses the same tokens from scratch; on a grammar Python's size that is exponential. A memo keyed by `(rule, token_pos)` in the `Parser` base class makes parsing linear *and* is the substrate left recursion needs. Unsound without the derived element list (§3.7): replayed results must not depend on push chronology. **Do this second.**

   **STATUS: DONE (2026-07-03).** Every generated `Parse_<Rule>` (sequence and either) is now a memo wrapper around the renamed `Parse_<Rule>_Rule` body; the `Parser` base class holds the table (`Memo`) and `Memo_Get` / `Memo_Replay` / `Memo_Store` (`Parse_Memo` entries cache success, produced element objects, end positions). Replay pushes the *same* element objects, so the tree — and the §3.7 derived list — is identical to a fresh parse; failure replay needs no position restore because rules roll back before returning false. For gal's own backtrack-free grammar the memo never hits (fixpoint held byte-exact, five artifacts); on `python-3.11.gram` the peg parser dropped from 0.94s to 0.42s. Known cosmetic gap: a memoized-failure replay skips `Rollback`'s error stamping — superseded by Tier 3 farthest-failure tracking when it lands.
2. **Left recursion.** `expr: expr '+' term | term` infinite-loops in plain recursive descent. The standard fix (pegen / Warth seed-growing) builds directly on the memo table. Seed-growing creates and discards partial trees; the §3.7 walk guarantees only the final tree reaches the inference engine. **Do this third, on top of memoization.**

   **STATUS: DONE (2026-07-03).** Warth-style seed-growing with **dynamic detection** — no grammar annotation needed. The memo wrapper plants an `In_Progress` seed before running a rule body; a rule that reaches its own seed fails that attempt (letting the base-case alternative win) and sets `Detected`, which triggers the grow loop: re-run the body from the start position while the match keeps advancing, replaying the previous iteration at the recursion point. The crucial subtlety is **indirect** recursion, which gal's rule shape *forces*: the Grammar→gal generator splits `expr: expr '+' term | term` into `either Expr` + `sequence Expr_Plus`, turning every direct left recursion into a two-rule cycle whose middle rule memoizes a seed-dependent (polluted) result. Handled by recorder-based invalidation: from the moment recursion is detected, every memo entry *settled* while the seed is live is recorded (the head's own entry excluded) and invalidated before each grow iteration. Zero cost unless recursion actually occurs — for gal's own grammar the machinery never fires (fixpoint held byte-exact, five artifacts; peg unchanged at 0.44s). Validated by `examples/leftrec.txt`: `1 + 2 + 3` → `Lrec_Plus(Lrec_Plus(1 + 2) + 3)`; a 12-operand chain nests 11 deep left-associatively; degenerate and failure inputs behave.
3. **Stateful lexer layer.** The `tokens` statement only *selects* which existing token classes to accept; it cannot express INDENT / DEDENT / NEWLINE, which are stateful. Python needs a real lexer stage. This is the one piece that cannot be a pure PEG rule. (Note: gal3 already unifies lexing and parsing — `parser Gal_Token` — but indentation tracking is stateful and sits outside that model.)

   **STATUS: DONE (2026-07-03).** `py_base.txt` + `py_main.txt`, artifact `pylex` (in `./build`, `selfbuild`, `selfself`; fast iteration via `./pybuild`). Token element classes (`Py_Name`/`Py_Number`/`Py_String`/`Py_Op`/`Py_Newline`/`Py_Nl`/`Py_Comment`/`Py_Indent`/`Py_Dedent`/`Py_Endmarker`) use the proven `Factory`/`Append_Character` state-machine pattern — the same de facto architecture as gal's own lexer (note `parser Gal_Token` exists but is not the exercised path; `Token:Factory` is). The line discipline lives in `Py_Compiler`: indentation stack with tab-to-8 columns, paren/bracket/brace depth for implicit joining, backslash joining, blank-line suppression, retroactive string-prefix merging, EOF flush. Significant tokens and trivia are separate positional lists per §7. **Oracle: CPython's own tokenize module** (`bin/pylex_oracle.py`) — 50 of 52 stdlib modules lex byte-identically (>100k tokens); the two failures use PEP 701 nested same-quote f-strings, which Python 3.11 itself rejects (the pin working as designed). ~16k tokens lex in 0.2s. Found and fixed along the way: gal3 lacked `mod` (added `Operation_Modulo` to dialect + all three generators); the dialect lacked the `'class property ='` verb alias so initialized class properties mis-bound on reparse; and gal3's `Operation_Or`/`Operation_And` Python and JS generators dropped chained operands beyond the first two (the leftover keyword tokens in `Listargs` are `Token_Word`s, now mapped explicitly to the target-language operator).

### Tier 2 — blocks practical / clean use
4. **Captures and node-shaping.** `sequence` currently keeps *everything* matched in `My_Elements`, including literal `:` `,` `(` tokens — a cluttered CST, not a usable tree. Python's `a=expr` named items want labeled captures and the ability to discard literals. This is the CST→AST jump: a real DSL evolution (new syntax + generator changes).
5. **Inline grouping.** Either the generator lifts nested groups into synthetic rules (§4), *or* inline groups are added to the DSL. Adding them to the DSL is more work up front but makes the generator far simpler and the DSL pleasant to hand-write.

### Tier 3 — quality / will bite eventually
6. **Farthest-failure error tracking.** `Rollback` just stamps `Top.Error` at the current position; there is no "deepest position reached," which is *the* mechanism for non-useless PEG error messages. Pairs with the existing line-number TODO.
7. **Positive lookahead `&e`** and **cut `~`.** `!e` exists via `exclude`, but the `Syntax_Exclude` generator still contains a `debug;` and a "right?" comment — **prove that path before relying on it.** `~` only affects error quality and backtracking bounds; it can be ignored for a recognizer.

## 6. The normalized generator

**Philosophy.** Output is *normalized*, not byte-identical. Normalization makes code more consistent; a programmer who does not want their code reformatted simply does not run it through the parser/generator. This is the same thing gal already does for itself — the `Gal` generator and `Infer_Gal` methods reprint from structure with spacing rules rather than copying source spans.

**Architectural payoff.** Because normalization is a generation-time concern, the element tree does **not** need to be a lossless CST. It can be a clean AST with comments attached as trivia. All whitespace policy lives in one place — `Python_Generator`. The parser's fidelity obligations shrink to three:

1. **Lex strings and comments as opaque tokens** — interiors never touched, so `""" … """` and all string contents survive automatically.
2. **Attach comments to elements as trivia.**
3. **Emit NEWLINE / INDENT / DEDENT** so block structure is in the tree.

Everything else is regenerated. `Get_Input` (the per-element source span) becomes a debugging aid, not the regeneration mechanism.

### 6.1 Normalization decisions

- **Space consolidation.** Redundant spaces outside literals and comments are collapsed: `print(   X  , Y )` → `print(X, Y)`.
- **String literals** — preserved exactly, including triple-quoted blocks. Interiors are opaque.
- **Comments** — interior spacing preserved, trailing whitespace trimmed: `#   this   is   a   test   ` → `#   this   is   a   test`.
- **Indentation** — normalized to **4 spaces per level**, regardless of original (tabs, 2-space, 3-space, 8-space). This is a generator preference; the generator may offer multiple line-wrapping/indentation strategies for long lines.
- **Blank lines** — Python is opinionated; blank-line policy lives in the generator.

### 6.2 Why indentation normalization is safe

Python's INDENT/DEDENT tokens encode only *relative nesting depth*, never absolute columns. Mapping any consistent scheme to 4-spaces-per-level reproduces the exact same INDENT/DEDENT sequence — so there is **no semantic drawback**, only the imposed-style one (accepted by design). Tabs→4 is doubly safe: Python 3 forbids inconsistent tab/space mixing, and PEP 8 prefers 4 spaces.

### 6.3 The real iceberg: continuation-line reflow

Whitespace inside `()[]{}` or after `\` is **not** indentation — physical lines are implicitly joined into one logical line *before* the offside rule runs, so this whitespace falls in the "consolidate spaces" bucket, not the "4-space level" bucket:

```python
result = some_function(arg1,
                       arg2)
```

This has no INDENT to normalize; instead the generator must **reflow** it — join it, or apply a line-wrap / max-line-length policy. This reflow decision (not indentation) is where essentially all of a normalizer's real difficulty lives. "Normalize indentation" quietly drags in "define a statement-reflow policy"; decide them together. The generator may expose wrapping as a preference with multiple strategies.

### 6.4 Known cosmetic gotcha (accepted)

Renormalizing block indent (e.g. 2→4) shifts the *code*, but a multi-line `""" … """` whose interior was hand-aligned to the old indentation stays put (string content is preserved exactly). The docstring can end up visually misaligned relative to its reindented code. This is cosmetic, not semantic, and unavoidable without editing string content — which we forbid. **Decision: accept it.** Solving it may not be an improvement, and Black makes the same trade-off.

### 6.5 Comment attachment (resolved 2026-07-05 — default heuristic adopted)

The genuinely fiddly part of normalized regeneration — more than indentation — is deciding whether a comment is a **trailing** comment of the line it sits on, a **leading** comment of the next statement, or a **standalone** block. **Decision: the default heuristic, applied mechanically; future edge cases may tweak the rule, and this is a candidate for LLM inference eventually.**

Implementation (in `pygen`): **comments attach to tokens.** A comment on the same physical line as code (previous significant token is not a NEWLINE/INDENT/DEDENT and no newline intervenes) is *trailing*: it rides on the `Py_Newline` token ending its line and regenerates as `  # text` (PEP 8's two spaces) before the newline. A comment on its own line is *leading*: it rides on the next emitted significant token and regenerates as its own line(s) directly before that token — and because leading comments are emitted inside the token's text, the block indenter places them at the following statement's indentation automatically. A comment **inside brackets** — which implicit-line joining would strand mid-expression — *hoists* to lead its logical line's first token, one line per comment, preserving multiplicity and order (v1 folded them into the trailing position, but re-lexing merges adjacent trailing comments, losing count). Comments before EOF ride the ENDMARKER. Trailing whitespace is trimmed (§6.1); interiors are verbatim.

The corpus oracle gained a third check — **comment preservation** (the multiset of comment texts must survive regeneration) — alongside `ast.dump` equality and idempotence: **49/49 stdlib modules pass all three.** One engineering note: the quote-aware block indenter must also be *comment-aware* (a `#` outside a string suppresses quote tracking to end of line), or an apostrophe in comment prose opens a phantom string and dedents everything after it — the third appearance of the quote-poisoned-indenter bug family in this project.

## 7. Next concrete artifact: the token & trivia model

Since normalization is a generator concern and the parser's job reduces to the three obligations in §6, the foundation everything depends on is the **token + trivia model**. It constrains the lexer, the element tree, and the generator simultaneously. It comprises:

- The Python token class hierarchy as gal element classes: `NAME`, `NUMBER`, all string-prefix variants (`r` / `b` / `f` / `rb` / …), `OP`, `COMMENT`, `NEWLINE`, `INDENT`, `DEDENT`, `ENDMARKER`.
- Which channels are **trivia** (comments, insignificant whitespace) vs significant tokens.
- The **comment-attachment rule** (§6.5).

This piece has the most downstream leverage and does **not** commit us to the Tier-1 engine work yet.

## 8. Open decisions

- **Comment attachment heuristic** (§6.5) — unresolved.
- **Continuation-line reflow / line-wrap policy** (§6.3) — needs a default plus optional strategies.
- **Left-recursion strategy** — grammar rewrite vs. engine support (seed-growing). Engine support is preferred for generality but is the larger build; defer until the element tree is visible.
- **Engine scope** — general PEG engine (packrat + left recursion + captures + lookahead) vs. minimal-for-Python. They largely converge; the main divergence is captures/node-shaping, which a recognizer does not need but a translator does.

## 9. Sequencing and milestones

The guiding principle is to prove each layer against a built-in oracle before building the next.

1. **Initiative 1 — PEG metagrammar parser.** Write `parser Peg` in the gal DSL, define the Grammar IR element classes, and parse the real Python grammar file. **Milestone: dump the parse tree** (`To_String`). This needs little or no engine evolution (a grammar file is well-behaved — no left recursion, no INDENT/DEDENT) and validates the DSL on real external input. Also proves or disproves the `exclude`/lookahead path (§5, Tier 3). Note: the Grammar IR elements themselves are parsed by a generated parser and processed by inferences, so they rely on the §3.7 element-order contract like everything else.

   **STATUS: DONE (2026-07-03).** `peg_base.txt` + `peg_main.txt`, built as the `peg` artifact (`./build` or the fast `./pegbuild`). Parses all 229 rules of the vendored `grammars/python-3.11.gram` in ~0.8 s (no memoization needed at this scale) and dumps the full tree; construct counts verified exact against the source (forced tokens 9/9, cuts 6/6 — the 7th `~` in the file is the quoted `'~'` invert operator, correctly a string). Findings: (a) the pegen metagrammar needed **no** `exclude`/lookahead at all — that path remains unproven, deferred to when a grammar actually needs it; (b) ordered choice with real post-consumption backtracking (`a[T]=x` vs `a=x` vs bare `a`) works correctly through the existing rollback machinery; (c) the tokenizer needed Python-style **implicit line joining** (newlines inside `()`/`[]` are insignificant) because grammar groups span physical lines; actions `{...}` and strings are opaque string-aware blobs.
2. **Token & trivia model** (§7) — the foundational artifact for everything Python.
3. **Engine: derived element list, then memoization, then left recursion** (§5, Tier 1) — each step validated against gal self-hosting (must still fixpoint byte-exact).
4. **Stateful Python lexer** (§5, Tier 1) — INDENT/DEDENT/NEWLINE, opaque strings and comments.
5. **Grammar→gal generator** — emits `parser Python` + element classes, with rule-lifting (§4).

   **STATUS: DONE (2026-07-03).** `peg_gen.txt` extends the peg artifact: `peg.py grammars/python-3.11.gram python_parser.txt` emits 416 sequences (each with an element class, real rules `is Py_Rule`, synthetics `is Py_Synth`), 125 eithers, and 61 hand-emitted methods — the `&e`/`!e` lookaheads (parse into a scratch list, always roll back, return possibly-negated result; this permanently supersedes the never-proven `Syntax_Exclude` path) plus `Parse_Py_Name` with reserved-keyword exclusion (pegen's NAME semantics). Methods are emitted *inside* the `parser Python { }` block because the parser statement copies member statements into the generated class — `class set` cannot target a class that only exists in generated output. Erasures: actions, annotations, cut, forced (error-quality only); `invalid_` rules and their referencing alternatives (pegen second-pass only); `ASYNC`/`AWAIT` map to literals, `TYPE_COMMENT` to a never-produced token (≡ `type_comments=False`). The `pyparse` artifact (lexer + generated parser + support) **must be compiled by the gal3 chain** — memoization and seed-growing live in gal3's generators, and a gal2-built parser stack-overflows on `t_primary` immediately; pyparse is the first artifact gal2 structurally cannot build. **Result: 49/49 of the 3.11-compatible stdlib modules are accepted** (the one excluded module, `typing.py`, uses PEP 695 generics — 3.12+ syntax), and the parser reproduces CPython's acceptance boundary (an invalid unparenthesized walrus is rejected at the same token CPython rejects it). ~6s per stdlib file after the fix below.

   **Engine insight from this step (left-recursion invalidation must be position-scoped).** The first pyparse was correct but catastrophically slow (118-line file: 36s; 610 lines: 464s) because grow-loop invalidation cleared *every* memo entry settled during the seed window at *any* position, forcing each grow iteration to re-parse whole expression subtrees. Since PEG positions only move forward, an entry at a later position can never consult a seed at an earlier one — **only same-position entries can depend on the seed**. Restricting recording/invalidation to entries whose start position equals the head's (the recorder stack now holds head entries, and settles filter by position) restored near-linear parsing: 54–420× faster on the probe set, leftrec regression unchanged. A `High_Water` mark in `Consume_Token` (farthest consumption, surviving rollback) was also added so failed parses report where they actually stalled — the first installment of Tier 3 error tracking.
6. **`Python_Generator`** — normalized regeneration (§6).

   **STATUS: CORE DONE (2026-07-04).** `pygen_base.txt` + `pygen_main.txt`, artifact `pygen` (gal3-chain compiled, in all build scripts; fast `./pygenbuild`). Because the parse tree is a CST that kept every token — including the synthetic NEWLINE/INDENT/DEDENT leaves — **one generic generator body covers all 541 element classes**: an element regenerates as its children joined by a token-pair spacing policy (`Normpy_Glue`); a token regenerates as its text; a `Py_Indent`…`Py_Dedent` child pair brackets an interior that gets quote-aware 4-space-per-level line prefixing (triple-quoted interiors untouched — the §6.4 accepted trade-off, by construction). Synthetic elements are transparent pass-throughs automatically. Continuation-line joining (§6.3's default policy) also falls out: non-logical newlines were trivia, so multi-line calls regenerate as one logical line. **Oracle: 49/49 corpus modules pass both checks** — `ast.dump` equality (CPython confirms meaning unchanged) and byte-exact idempotence (normalize∘normalize = normalize) — **with the override table still empty**. Multi-alternative rules now get abstract base classes that their alternative-synthetics inherit, so future context-dependent overrides (`generate Python_kwarg_or_starred` for tight `=`, unary minus, slice colons — currently valid-but-not-PEP8) have stable names that reach every alternative through inheritance. Not yet done: comment/trivia reattachment (§6.5, the open design question) and PEP 8 spacing refinements; both are oracle-guarded increments.

   **The cross-language path (decided in review, 2026-07-04):** mirroring the gal compiler's own two-layer architecture — where the parser emits general elements (Statement, Operation) and a *classification inference* specializes them (Statement_Class, Operation_Add) — normalized Python regeneration runs off the general grammar-rule classes (the CST has every detail), and a future **Python classification inference** maps elements onto specific classifications (e.g. `Python_Function_Print`) as the bridge for generating into other languages, reusing exactly the per-classification generator machinery the gal compiler already uses.
7. **End-to-end oracle: Python → elements → normalized Python**, on a real subset, with the normalized output as the correctness check (the analogue of the self-hosting fixpoint). Cross-language (C) and full-grammar coverage follow once the skeleton is proven.

   **STATUS: DONE (2026-07-05)** — steps 6 and 7 together: the pygen oracle (`bin/pygen_oracle.py`) runs `ast.dump` equality, comment-multiset preservation, and byte-exact idempotence over the corpus; 49/49 stdlib modules pass.

8. **Classification & translation: Python → gal3 (`pygal`)** — see §10. The bridge to cross-language generation; C follows once the gal3 path is proven.

## 10. The classification step: Python → gal3 (the `pygal` artifact)

**Decided in review, 2026-07-05.** Milestone 1 is the **full loop with a behavioral oracle**: classify a tiny-program subset, emit gal3 source, extend the gal3 compiler dialect with the Python-specific element classes and their fallback lowering, compile the emitted gal3 through the existing chain (`gal.py` → `fallback.py`× → `galpy.py`), run it, and compare stdout against CPython running the original. Nothing lands unverified. The **next-phase corpus** after the tiny program: the gal3-generated Python artifacts themselves (`galpy.py`, `fallback.py`, …) — machine-generated Python in a constrained style, and the first step toward a gal3 → Python → gal3 round trip.

### 10.1 Architecture — mirroring the gal compiler exactly

`pygal` is a new artifact (zero + `py_base` + `pyparse_base` + `python_parser` + `pygal_base` + `pygal_main`), a sibling of `pygen` on top of `Py_Parse_Compiler`. Its pipeline mirrors the gal compiler's parse → classify → generate:

1. **Parse** — the existing generated `Python_Parser` produces the CST.
2. **Classify** — a bottom-up pass (forward over the §3.7 derived list) sets each CST element's `Classification`. The default is **transparent adoption**: an element with exactly one significant child adopts that child's classification — this collapses the deep single-child rule chains (`expression` → `disjunction` → … → `atom`) for free, the classification-layer analogue of the synthetic pass-through rule (§3.7). Per-construct overrides on the grammar-named CST classes build **`Pyc_*` classification nodes** (a semantic AST: `Pyc_Funcdef`, `Pyc_Assign`, `Pyc_Call`, `Pyc_Add`, …) wired to the child classifications.
3. **Emit** — derive a post-order flat list of the `Pyc` tree (reusing `Walk_Element`) and run a bottom-up gal3-text inference over it, exactly like every other generator in the system.

Per §3.4 this layer is hand-authored, construct by construct — that is the irreducible semantic work, and why it grows subset-first rather than grammar-generated.

### 10.2 The structure / leaf-semantics split

§3.6 forbids equating Python constructs with gal constructs *in the element model*. At **emission** the rule adopted is:

- **Pure structure maps to gal directly**: blocks, `main`, the module wrapper class, method declarations, `return`, assignment (Python rebinding ≡ `variant` declaration + assignment), `if`/`elif`/`else` shells.
- **Anything carrying Python semantics becomes a Python-specific gal3 dialect element**, whose equivalency to gal atomics lives in the gal3 compiler's *fallback generators* — §3.6's mechanism, and the crucial property for C: a future C target overrides the same classes (e.g. polymorphic `py+`) without touching pygal.

Milestone-1 dialect additions (verbs prefixed `python` / `py`):

| Python | gal3 dialect element | fallback lowering |
|---|---|---|
| `print(a, b)` | `python print A B;` (`Statement_Python_Print`) | `say` with `' '` separators, stringified args |
| `while c:` | `python while (C) { }` | `forever { break if (not C); … }` (gal has no while) |
| `for i in range(n):` | `python for range I N { }` | `for I range 0 (N - 1) { }` |
| `+ - * / %` | `py+ py- py* py/ py mod` (`Operation_Python_Add`, …) | gal `+ - * / mod` |
| `< > <= >= == !=` | `py< py> py<= py>= py== py!=` | gal comparisons |
| `and or not` | `py and` `py or` `py not` | gal `and or not` |
| `str(x)` | `py str` | `(string X)` |

Declarations go in `compiler_dialect.txt`, generators in `fallback_inference.txt` (both clearly sectioned — generator blocks cannot be reopened from a separate file). The classes lower away entirely in the fallback stage, so no Python/JS generator changes are needed. This touches the core compiler sources, so the **self-hosting fixpoint must be re-verified** after the change.

### 10.3 Program shape and milestone-1 restrictions

Module-level `def`s become methods of an emitted wrapper class; top-level statements become `main`, which instantiates the wrapper and calls methods for module-function calls. pygal keeps per-scope symbol tables: a name's first assignment in a scope emits `variant X (expr);`, later ones plain assignment. Accepted milestone-1 restrictions (each is a documented gap, not a design limit): functions use only parameters and locals (no globals); conditions are real comparisons (Python truthiness of non-booleans — a future `py bool` operation); string literals are escape-free (gal string literals do not process escapes, so `'a\nb'` would need decoding into real control characters at emission — future work).

### 10.4 Oracle

`bin/pygal_oracle.py`: run the original `.py` under CPython, run pygal → gal3 chain → generated `.py`, compare stdout byte-exact. First driver: `examples/pysmall.py` exercising the whole subset. Plus the standing regression: the fixpoint must hold after the dialect extension.

### 10.5 Milestone 1 status

**DONE (2026-07-05).** The full loop passes: `examples/pysmall.py` translates (`pygal` artifact, `./pygalbuild` fast path), the emitted gal3 compiles through the chain, and the output is byte-identical to CPython — and the emitted program is essentially the hand-written reference rendition (`examples/pydialect.txt`, the lowering regression test that validated the dialect extension before the translator existed). All the §10.2 dialect elements are in `compiler_dialect.txt` with fallback lowerings in `fallback_inference.txt`; classification and emission are `pygal_base.txt` + `pygal_main.txt`; pygal is wired into `build`/`selfbuild`/`selfself`.

**Three latent gal3 codegen bugs found and fixed along the way** (the 6th–8th found by this initiative, all invisible to the fixpoint because both generations were consistently wrong — the functional gates caught them):

1. **`Operation_Divide` had no Python or JavaScript generator** — only a precedence entry. The compiler sources never divide, so it was never exercised. Symptom: any statement containing `/` silently lost its target text and its whole enclosing block generated as `pass`.
2. **Operator-precedence parenthesization never fired**: `say ((1 + 2) * 3);` compiled to `print(str(1 + 2 * 3))` — a genuine miscompilation (7, not 9) that survived because compiler sources happen never to nest higher-precedence operations under lower ones. Two independent causes: (a) the per-operation `class set Operation_X { property integer Python_Precedence n; }` tables were **silently dropped** — a `class set` targeting a dialect-generated class matches nothing, because the class only exists in generated output (the same limitation that forces parser methods to be emitted inside the `parser` block; it should probably become a loud error). The values now live as `property` members **inside the operation declarations** in `compiler_dialect.txt`, which demonstrably materialize. (b) Even with values present, the readers compared the *parse element's* precedence (always 0, since arguments captured during top-down classification are parse elements) — fixed by dereferencing `[Arg.Classification]`, plus the associativity refinement: right operands parenthesize at *equal* precedence too (`10 - (4 - 3)`).
3. (Consequence of 2 being fixed:) chained `and`/`or` mixes now regenerate with correct grouping — previously `a and (b or c)` regenerated as `a and b or c`, which parses differently and only coincidentally evaluated the same in the sources that existed.

**Engine note for the classification layer:** interior synthetics inherit their rule's class (deliberately, for rule-scoped generator overrides), so a `Pyc_Build` handler on a single-alternative rule class also fires on that rule's `_O`/`_P` interior synthetics. Handlers on such classes guard on the exact class name and fall back to the default build; handlers on alternative classes (`_A`) are safe because interiors inherit the abstract rule base, not the alternative.

### 10.6 Phase 2: covering gal-generated Python (in progress; wave A DONE 2026-07-05)

**Decided in review:** the approach must cover the language elements gal itself creates when generating Python output — if it cannot eat `galpy.py` and friends, it is not on the right track. An AST census of the nine gal3-generated artifacts shows the surface is **closed and small**: ~35 node types, no comprehensions/lambdas/decorators/yield; builtins are `str`, `len`, `super`, `Exception`, `print` (181 with `sep=`), `isinstance`, `range`, `open`; everything else is plain method calls, which the generic `Obj.Method args` emission covers without per-method work.

**Wave A (DONE):** classes with single inheritance and methods (`self` stripped, `self.x` ↔ `[my x]` / `Obj.x` propset), instantiation via a module-class registry, method calls (`i M` inside methods), attribute access, `break`/`continue`/`pass` (classified at the token — they are bare literals in the grammar with no rule element), `while True`, the `if __name__ == '__main__'` guard (its suite splices into `main`), subscript load/store (`py sub` / `python setitem`), `is`/`is not`/`in`, `len`/`isinstance` (`py len`/`py isa`), list/tuple/empty-dict literals, one- and two-argument `range`, `print(..., sep='')` (`python print0` → `say`), imports elided (galpy regenerates its own), **string escape decoding** (python escapes → real characters → gal literals via `[line]`/`[tab]`/`append` composition, since gal strings never process escapes), and **f-strings**: split into literal runs and expression segments, each expression **sub-parsed by a child compiler** through `Parse_Python_expression` and classified with the same machinery. Names already valid as gal names pass through verbatim (machine-generated python round-trips readably); invalid ones get a `Py_` prefix; method/attribute names are never mapped (attribute namespace — `append` etc. must survive).

**Oracle extended with self-application:** after a file passes, its generated Python — genuine gal3-generated output — is fed back through the whole loop. `pysmall.py` passes both generations byte-identically; the second-generation gal3 correctly reconstructs sub-parsed f-string interiors like `(py fstr (py * 6 7) ' ' (py - 10 3) …)`.

**Engine gotcha found by the sub-parser:** after a top-level `Parse_Python_expression`, the parser's chronological element list ends with orphans from discarded left-recursion grow iterations — `llast` is *not* the root. The winning root is the element the parse pushed into the caller's list; derive the flat list by walking that tree. (The whole-file parse is immune: the file element genuinely completes last.)

**Wave B (DONE 2026-07-05):** the census's remaining constructs, each grounded in the exact shape galpy emits. `try`/`except` → `try`/`catch` — with **inverse idiom mapping**: the corpus's `raise ValueError` and `except (ValueError, AttributeError)` turned out to be the compiled forms of gal's own `defined`/`undefined` statements, and `except Exception: pass` is `forgive`, so those try-shapes classify back to the very statements that produced them (the second-generation gal3 literally reads `defined Py_d { … }`, `forgive { … }`). `raise Exception(msg)` → `python raise`. `def __init__` → `constructor`, dropping a leading `super().__init__` (gal chains automatically) and supporting `=None` parameter defaults (`[variant A [null]]`) — the emitted `Base` prelude now carries the same three-slot argument-sink constructor as `compiler_base`, since translated constructors chain into it. `+=`/`-=` desugar to load-op-store (equivalent for the strings and numbers the corpus applies them to; lists use `.extend`). `for x in <iterable>` → `for each`; `for k, v in d.items()` → `iterate` (the tuple target flattens to two leading names). Two-bound slices → `py slice`. Attribute chains collapse to bracket chains (`self.A.B` ↔ `[my A B]`, `X.A.B` ↔ `[X.A B]`), as loads and as stores. Method-call targets generalize to any expression (`', '.join …` works). Class-method names stay verbatim on both declaration and call site (module functions still map through the registry). Oracle: `examples/pysmall2.py` exercises the whole set — **both test programs pass both generations byte-identically**.

Wave B engineering notes: `try` was missing from the python-keyword list (the stray `Pyc_Name('try')` shifted every try-statement's kids); f-string expression scanning needs bracket-depth and quote tracking, because `{ x[2:5] }` has a colon that is *not* a format spec; galpy's same-line suites (`except Exception: pass`) produce no block element, so a bare statement must be wrapped into a suite; and `list PN [obj prop]` *copies* in gal3-generated Python — mutate through the bracket property directly.

**Still open after the first artifact:** `with open(...)` write idiom (`Statement_Write_To`'s shape — pylex used `Runtime.File_Dump` instead), the `Value=` keyword argument (21 uses, not in pylex), multiple `defined` guards in one idiom, `sorted`, non-`classmethod` decorators.

### 10.7 First real artifact: pylex round-trips (DONE 2026-07-05)

**`pylex.py` — the 226 KB gal2-built Python lexer artifact — translates to gal3, recompiles through the gal3 chain, and the recompiled lexer produces byte-identical token dumps** on `string.py`, `bisect.py`, `heapq.py` (stdlib) and the test programs. Translation takes ~37 s (parse dominates; memoization scales fine at this size). `bin/pygal_artifact_oracle.sh <artifact.py> <inputs…>` is the standing oracle. Emitted programs are now wrapped in `module Compiler { … }`, which gives `Statement_Main` its required module context and activates dynamic includes.

The artifact needed five construct additions (classmethod decorators → `class method` with `cls` stripped; class-level property assigns → `class property` declarations; the `sys.argv` try-idiom → `main [string A, string B]`; the `_FH = open/read/close` triple → `fread`; `zdebug.zbreak()` → `debug;`; bare `self` → `[self]`; `X in string.punctuation` → `(X is punct)`; the compiled `End+1` range marker → gal's inclusive `for range`, which also keeps round trips from accreting `+1-1` chains) — and it flushed out **three more latent gal3 bugs** (9th–11th):

9. **`Syntax_Return.Unquoted` held the two characters `\` `r`** instead of a real carriage return, in both Python and JavaScript inference — the same no-escape-processing trap the design notes for `[line]`, never caught because nothing had ever put `[return]` through an append. Fixed with a new `Runtime.Chr` helper (gal2 has no `[return]` literal syntax, so the generator cannot use it during bootstrap).
10. **`Python_Escape_Content` (and the JS escapers) never escaped carriage returns**, so a real CR in a literal landed raw inside a generated f-string — a syntax error. Both now emit `\r`.
11. **gal3-built programs that call `Runtime:*` got no `from Runtime import Runtime`** — the gal2-built artifacts mask this with gal2's static import header, but the gal3 chain emits only dynamic includes and no generator ever added Runtime's. The four call generators now add it whenever the receiver is `Runtime` (inside a module).

One more gal-language gotcha recorded: `[X.Method]` is property access — it compiles to a bound-method *reference*, not a call; `(X.Method)` is the call form. An include hook silently never fired because of this.

---

*This document records a design discussion and is intended for review before implementation begins.*
