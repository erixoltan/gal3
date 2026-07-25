# abstraction inference — design

*Draft 2026-07-20. Companion to [abstraction_inference.md](abstraction_inference.md),
which states the original concept and why it is the missing component of gal.
This document is the design: how abstraction inference fits the gal3
architecture, what the rule notation is, how correctness is checked, and the
milestone ladder that gets there. Nothing here is built yet.*

## 1. What it is: the fourth arrow

The pipeline today runs in one direction — abstraction is *lowered*, never
raised:

```
  program.gal ──(fallback, repeat to fixpoint)──▶ program.atomic ──(target)──▶ program.m
```

Abstraction inference is the dual arrow: an **entity inference** that walks a
list of fully-classified low-level elements and creates new, higher-level
elements to represent recognized regions of them.

```
  program.m ──(front end)──▶ elements ──(lift, repeat to fixpoint)──▶ program.gal
```

Where a fallback lowering *expands* one composite element into a sequence of
simpler ones, an abstraction rule *matches* a sequence of simpler elements and
replaces it with one composite. The two are inverses, and the design leans on
that inversion everywhere: for the rule notation, for the correctness gate, and
for the training corpus.

Like fallback, lifting runs in **rounds to a fixpoint**: each pass lifts the
innermost regions whose members are already fully lifted, and the loop repeats
until a pass changes nothing (capped, as the fallback loop is). Nesting —
if/else inside loops inside if/else — comes free from the rounds, exactly as it
does going the other way.

The working name for the artifact is **`lift`**, built like every other
artifact: zero stack + `gal_base` + `lift_inference` + `lift_main`, emitting
gal. (`abstract` is a poor artifact name; it collides with the statement-kind
vocabulary below.)

## 2. Design decisions

### 2.1 The rule notation is the parse-rule notation, one level up

The concept doc asks what notation could represent "a sequence of instructions
with arbitrary things in the middle but certain things excluded." The answer is
already in the language: **abstraction is parsing, where the tokens are
language elements.**

The `sequence` / `either` rules turn a list of tokens into elements. An
abstraction rule turns a list of elements into a higher element. Same shape:
required items in order, holes (`repeating`, `optional`), ordered alternatives
(`either`). The combinatorial explosion that blocked the 1987 design is the
problem recursive descent already solves: once `Lifted_Statement` is defined
recursively (an `either` over every lifted construct plus the local-flow-only
atoms), arbitrary nesting needs no per-combination rules.

The "forbidden things" constraint falls out for free. A region's inner
alternative set simply does not include a goto whose target is outside the
region — a foreign goto fails the match and the region stays unlifted. No
separate forbidding machinery is needed.

Proposed surface form: a new statement kind `abstract`, mirroring `generate`,
declared per composite element per source level, and spliced onto the
composite's class by sideways inheritance from `lift_inference.txt` — the
exact structural discipline the backends already use for `generate`. Sketch
(syntax is illustrative, not final — see open questions):

```
abstract Statement_Break_If
{
    match Statement_If Cond;
    match block exactly { Statement_Break; }
    match no else;
    lift 'break if ' Cond ';';
}
```

Semantics: when the matcher recognizes an atomic `Statement_If` whose block is
exactly one `Statement_Break` and which heads no else chain, replace it with a
`Statement_Break_If` carrying the same condition. The `lift` clause is the
constructive half — it builds the composite element (or, equivalently in early
prototypes, emits the composite's gal source for reparsing).

### 2.2 Generators are already reverse patterns

The one-line generator form is a sequence of literals and argument slots:

```
mumps [indent] 'set ' Variable '=' Value [line];
```

Read forward it generates; read backward it is a pattern with two holes. Every
one-line `generate` implicitly defines its own `abstract` rule, and a later
optimization is to derive those inversions mechanically instead of writing them
twice. Scoped-form generators are not automatically invertible — but the
skeletons they emit are fixed. `mumps_inference.txt`'s `Statement_If` emits
precisely:

```
 if <cond>
 else  goto L<p>X
 <block>
 goto L<p>E
L<p>X ; if-else
[L<p>E ; end if]        ; when the chain ends here
```

and `Statement_For_Range` emits a fixed begin/continue/break label loop. Each
scoped generator's skeleton becomes one hand-written `abstract` rule with a
recursive block hole. The load-bearing pattern is the **label/goto shape**, not
the annotation comments (`; end if`, `; for range break`) — those may guide
debugging of the lifter but must never be matched on, or milestone 3 (wild
code, no comments) can never work.

### 2.3 Lifting is total: the goto-region element

The concept doc predicts regions that "do not add up to any well-defined higher
level language element." The design makes this a feature via one catch-all
composite: a **goto-region** element whose members are labels, gotos,
conditional gotos, and lifted statements, all first-class. Any region that
matches nothing lifts into a goto-region. Consequences:

- **Abstraction inference never fails.** Every input lifts to *something*
  semantically faithful; quality, not success, is the variable.
- **Improvement is monotone and measurable.** The score is *structuredness* —
  e.g. the fraction of gotos eliminated. Each new `abstract` rule or new
  language element can only raise it. This finally dissolves the combinatorial
  explosion pressure: no rule is ever *required*, so rules are added one at a
  time, each pinned by an oracle case.
- The goto-region needs a **fallback lowering** like any composite (it lowers
  back to its labels and gotos), which is what makes the round-trip gate
  runnable even on completely unstructured input.

### 2.4 Correctness is round-trip regeneration, tightening by milestone

The gate stated in the concept doc — the lifted program must regenerate the
original low-level code — is adopted directly, with the same byte-diff
discipline as the fixpoint:

| milestone | round trip | gate |
|-----------|-----------|------|
| M1 | `fallback(lift(program.atomic))` | byte-identical to `program.atomic` |
| M2 | `galmumps(lift(program.m))` | byte-identical to `program.m` |
| M3 | wild code gal never generated | semantic equivalence (normalize-and-diff, or execute both against test inputs) |

Byte-identity is achievable in M1/M2 because gal generated the low-level side
deterministically (M labels derive from `Start_Position` — no counters, no
nondeterminism). In M3 it is unachievable in principle (foreign label names,
foreign instruction selection), so the gate weakens to semantic equivalence —
and that weakening is exactly where the LLM enters (2.5).

As with the fixpoint, the round trip is a **structural** check: a lift that
loses information diffs dirty, but the gate says nothing about whether the
composite chosen is the *best* reading. Structuredness (2.3) is the quality
score; the oracles remain the behavioral check.

### 2.5 Rules and the LLM are stages of one loop, not alternatives

The concept doc poses "a notation, or an LLM analyzing the code?" as a fork.
The design answer is **both, in the loop already proven on data-type
inference** ([inference_process.txt](inference_process.txt)):

1. Rules lift everything they recognize (fast, deterministic, self-hosting).
2. Unmatched regions — goto-region residue — are handed to the LLM through the
   reserved seam (`llm_inference.txt`, `Infer_Intelligence`): *propose a
   higher-level gal program for this region.*
3. The proposal is **mechanically validated** by the round-trip gate. This is
   the property the 1987 design lacked and the one that makes LLM involvement
   safe: an LLM lifting is never trusted, only checked.
4. A human proofreads; accepted liftings are captured as test cases.
5. Recurring patterns in the accepted set are codified as new `abstract` rules
   (or new language elements, §4), moving them from the LLM to fast code. The
   LLM keeps only the tail.

This gives `Infer_Intelligence` its first load-bearing job.

## 3. Milestone ladder

Each milestone arrives with its ground truth already in hand, because **gal
generates matched high-level/low-level pairs at every stage of every build** —
the corpus problem that plagues decompilation research does not exist here.

### M1 — invert fallback (no new front end)

Lift **atomic gal back to composite gal**. `program.atomic` is already gal, so
the existing front end parses it; the new work is purely the entity inference,
the rule notation, and the fixpoint loop — built on home turf.

- Corpus: every `.gal`/`.atomic` pair the build has ever produced, including
  the compiler's own fourteen artifacts.
- First rules: the simplest structural inversions. `Statement_Break_If` /
  `Statement_Continue_If` (an `if` whose block is exactly `break;` /
  `continue;`), `Statement_Todo` (a `comment` whose text begins `"TODO: "`).
  Then climb toward the bigger lowerings.
- Gate: `bin/lift_oracle.sh` — for each pair, `fallback(lift(atomic)) ≡ atomic`
  byte-identical; report structuredness (here: count of composites recovered).
- Ambiguity shakeout: where two composites lower to the same atomic form
  (e.g. the return-if / if-return family), ordered choice picks; the round
  trip then verifies the pick re-lowers to the exact input. This is the small
  arena to get determinism policy (§5) right before M2.

### M2 — invert galmumps (gal's own spaghetti)

Lift the M code that `galmumps` emits back to gal; regenerate byte-identical M.

- Needs a small **M front end** (an `mlex`/`mparse` in the mold of
  `pylex`/`pyparse`; M's line-oriented syntax makes the lexer easy, and the
  emitted M is a disciplined subset).
- Rules: one `abstract` per control-flow skeleton in `mumps_inference.txt` —
  if/else-if/else chains sharing an end label, for-range label loops, for-each,
  break/continue as gotos to the loop's `K`/`C` labels, the `$etrap` forgive/
  try patterns, quit-as-return.
- Gate: extend `bin/lift_oracle.sh` — for each five-languages program,
  `galmumps(lift(program.m)) ≡ program.m`. Structuredness target: zero
  goto-regions on gal-generated M.
- Discipline: annotation comments are stripped before matching (2.2).

### M3 — wild code

M (or, later, assembly) that gal did not generate: no deterministic labels, no
skeleton guarantees, real residue.

- The rule set from M2 lifts what it can; goto-regions absorb the rest;
  the LLM loop (2.5) works the residue.
- Gate: semantic equivalence. Two candidate mechanisms, both worth building:
  **normalize-and-diff** (lift, re-lower, lift *again* — the second lift must
  reach the same gal, making gal itself the normal form) and **behavioral**
  (run original and regenerated code against test inputs — the oracle
  discipline, applied per program).
- This milestone is open-ended by nature; its measure is the structuredness
  score on a fixed wild corpus, ratcheting upward as rules and elements
  accumulate.

The grand gate, past M3, is the one the concept doc points at: the compiler
lifts its own generated output back to source-equivalent gal — the universal
translation engine closing its loop.

## 4. Residue as a source of new language elements

Structured-programming theory says every flow graph is expressible with
if/while alone (Böhm–Jacopini) — but for **irreducible** control flow
(multi-entry loops, crossing regions) only at the cost of duplicated code or
flag variables. Decompiler research fights this with heroic graph surgery
(Phoenix's pattern-independent structuring; DREAM's "no more gotos"; rev.ng's
control-flow combing) *because their output languages are fixed*: they must
force every graph into C.

gal has no such constraint, and this is the genuinely novel angle: **a new
language element costs one dialect declaration plus one fallback lowering.**
Backends never need to know it exists — fallback re-lowers it on the way out.
So when a residue pattern recurs — a loop with multiple exits to distinct
continuations, a shared tail entered from two regions, MUMPS's dot-block `do`
itself — the right move may be to *name it*: declare a composite that
represents it directly, give it a lowering, and let the lifter produce it.
The concept doc's prediction that studying these cases would yield "useful
additions to our existing programming constructs" becomes a concrete workflow:
M3 residue → recurring shape → new element → new abstract rule → structuredness
rises. Skycoding, run in reverse.

## 5. Determinism and ambiguity

- **Ordered choice.** The matcher is PEG-style, like the parser: alternatives
  try in declaration order, first match wins. No backtracking across committed
  lifts within a round.
- **Innermost first.** Rounds lift regions whose members are already fully
  lifted (or atomic), so a nested if lifts before its enclosing loop — the
  bottom-up direction of the element-order contract, applied to lifting.
- **Tiebreaker.** Among liftings that pass the round-trip gate, higher
  structuredness wins; declaration order settles the rest. The gate makes
  ambiguity safe: a wrong choice cannot survive re-lowering.
- **Overlap.** A rule consumes the elements it matches; a failed match consumes
  nothing. Two rules wanting overlapping regions is resolved by order, same as
  `either`.

## 6. Fit in the architecture

| piece | form |
|-------|------|
| artifact | `lift` = zero stack + `gal_base` + `lift_inference` + `lift_main`; emits gal |
| inference | a new **entity inference** in the driver, run in rounds to fixpoint (the mirror of the fallback stage's repeat loop) |
| rules | `abstract` statement kind in the dialect; per-composite rules spliced by sideways inheritance from `lift_inference.txt`, 1:1 with how backends splice `generate` |
| catch-all | goto-region composite: dialect declaration + fallback lowering back to labels/gotos |
| M front end (M2) | `mlex` + `mparse` artifacts in the mold of the Python toolchain |
| LLM seam (M3) | `Infer_Intelligence` / `llm_inference.txt`, per the probe → LLM → validate → capture → codify loop |
| oracles | `bin/lift_oracle.sh` (round trips + structuredness); regress cases pinned in `bin/regress_oracle.sh` as lifter bugs are fixed |
| self-hosting | `lift` is a gal program like every other artifact; it joins the fixpoint set |

## 7. Open questions

1. **Exact `abstract` syntax.** The sketch in 2.1 needs to be reconciled with
   the existing `sequence`/`either` machinery — is an abstract rule sugar over
   a `sequence` whose terminals are classifications, reusing the parser engine
   over `Parser.Elements` instead of tokens? That reuse is attractive and
   should be answered by prototyping M1.
2. **Element surgery vs. reparse.** Does a lift build the composite element
   in place (splicing the tree and re-deriving the flat list, as sideways
   inheritance already does), or emit composite gal source and reparse?
   Reparse is simpler and self-checking; surgery is faster. M1 can start with
   reparse.
3. **Names and comments.** Lifting recovers structure, not intent: variable
   names survive (M1/M2), but wild code's names may be meaningless and its
   comments absent. Semantic renaming is an LLM job layered on top —
   explicitly out of scope for the round-trip gate, since names don't affect
   it in M3 and would break it in M1/M2 if invented.
4. **How far down.** The concept doc starts at assembly. This design stops at
   M for now — M is the proving ground precisely because gal already writes
   it. Assembly needs its own front end and its own atomic dialect, but no new
   machinery: the ladder just gains a rung.
5. **Structuredness metric.** Goto-elimination fraction is the starting
   proposal; alternatives (region count, nesting depth recovered, composite
   density) should be evaluated once M2 produces real numbers.
