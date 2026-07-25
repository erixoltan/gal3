# gal3 against compiler and transpiler design theory

*Chapter 13 of the gal3 compiler design documentation — the systematic
compare/contrast that the paper's discussion section can be built from.
Per-mechanism comparisons live at the end of each chapter; this chapter
takes the whole-architecture view.*

## 1. Against the textbook pipeline

The dragon-book architecture and gal3 solve the same problem with opposite
commitments:

| dimension | textbook compiler | gal3 |
|---|---|---|
| representations | a chain of increasingly foreign IRs (text → tokens → AST → typed AST → IR → machine) | one representation: gal elements / gal text, at every stage including intermediates |
| formalisms | one per phase (regular languages, CFGs, type judgments, dataflow lattices) | one: an object hierarchy answering inference methods |
| phase output | consumed and discarded | accreted; characters, tokens, and positions survive to the end |
| construct dispatch | per-pass switch on node kind | per-class method, bound once at classification |
| grammar | defines the construct inventory | defines only shape; inventory is dialect data |
| lowering | desugaring before semantics; IR lowering after | semantic inference first, then source-to-source lowering to fixpoint |
| backend interface | orthogonal low-level IR | small set of *syntax-shaped* atomic elements |
| correctness | static discipline per phase + test suites | byte-exact self-compilation fixpoint + behavioral oracles + loud partiality |
| performance model | phases chosen for their cheapest machine (DFA, LALR tables) | uniformity chosen over machines; costs accepted |

The deep difference is **what varies and what is fixed**. A textbook
compiler fixes the language and varies the representation to suit each
algorithm. gal3 fixes the representation and varies the *language* — the
dialect, the composite element set, even the source language being ingested.
That inversion is the right frame for the whole paper: gal3 is a compiler
architected for a moving language.

## 2. Where each mechanism sits in the literature

Mapping each innovation to its nearest theoretical relatives, and what gal3
adds or trades:

- **Inference pipeline ↔ attribute grammars** (Knuth). Forward walks compute
  synthesized attributes, reverse walks inherited ones, over a topological
  (post-order) element order; `Data_Type`/`Usage` is literally the
  synthesized/inherited pair. gal3's departure: attributes are computed by
  arbitrary methods on an *open* class hierarchy, extendable from other
  files, rather than by equations closed over grammar productions. It gives
  up static circularity checking and gains open extension.
- **Inference pipeline ↔ nanopass** (Sarkar/Waddell/Dybvig). Both reject the
  monolithic pass; nanopass gets machine-checked per-pass IR invariants from
  closed IR definitions, gal3 keeps one open representation and makes passes
  partial (`forgive`) instead of total. Same taste, opposite ends of the
  static-guarantee spectrum.
- **Fallback lowering ↔ desugaring, macro expansion, and MLIR progressive
  lowering.** Unlike desugaring, it runs *after* full inference (so
  lowerings can be type-directed); unlike macros, it is per-class rather
  than per-call-site and needs no hygiene apparatus (it re-parses whole
  programs); like MLIR it lowers through user-extensible abstraction levels,
  but all levels share one human-readable representation. Normal form is
  reached empirically (iterate + `cmp`) rather than by proven confluence.
- **Shape parsing + classification ↔ lossless syntax trees and
  s-expressions.** Roslyn/rust-analyzer keep full-fidelity trees and layer
  semantics; Lisp fixes a trivial reader and puts the language in a
  dictionary of operators. gal3 combines them: an s-expression-like shape
  grammar with `;`/`{}` delimiters, head-symbol lookup *anywhere in the
  keyword sequence* (longest match), and full source fidelity retained
  underneath a parallel classification tree.
- **Dialects ↔ macro systems and language workbenches** (MPS, Spoofax,
  Rascal; Racket's `#lang`). Racket is the closest spiritual relative —
  languages as libraries — but gal dialects are compiled *into the next
  compiler generation* rather than expanded per program, keywords are
  dictionary data with no reserved words, and the same element hierarchy
  serves every dialect. Workbenches offer richer grammar variation; gal
  deliberately freezes the shape grammar to keep every dialect's output in
  one element algebra.
- **Sideways inheritance ↔ open classes / partial classes / inter-type
  declarations** (Ruby, C# partial, AspectJ, JastAdd). gal3's variant is a
  compile-time parse-tree splice executed at a defined pipeline position, in
  the language being compiled, with the flat-list re-derivation keeping
  single-pass inference sound. Its real significance is architectural: it is
  the answer to the expression problem that lets constructs × operations
  both stay open across concatenated files.
- **Parser engine ↔ packrat parsing and left recursion** (Ford; Warth et
  al.; pegen). Standard algorithms, with two engineering contributions worth
  stating: replay by *object identity* (memo entries store the produced
  element objects, so replays re-link the same tree), and **same-position
  invalidation scoping** for seed growth ("positions only move forward"),
  which made regrowth near-linear in practice. Plus the element-order
  contract: deriving the flat list from the winning tree is what keeps
  memoized, backtracking parses sound for the inference engine.
- **Bootstrap ↔ classical self-hosting and trusting trust** (Thompson;
  Wheeler's DDC). The four-generation source-replayable ladder is a
  DDC-friendly lineage; the byte-exact three-generation fixpoint across
  thirteen artifacts is an unusually strict form of the "compiles itself"
  milestone, and the explicit fixpoint/oracle separation (stability ≠
  correctness) deserves to be stated as a discipline.
- **Backends ↔ retargetable compilers and transpilers.** Against
  retargetable back ends (LLVM), the contrast is the syntax-shaped atomic
  set enabling *idiomatic* source output; against transpilers, the contrast
  is one pivot + N×M composition instead of per-pair tools, plus the
  cross-target byte-identical output oracle as the correctness criterion.
- **Universal translation ↔ UNCOL.** The classic objection — semantics leak
  through any fixed pivot — is answered by *dialect layering*: the pivot is
  extended with elements carrying the source language's semantics verbatim
  (`py +`, `python while`), and the semantic commitment is concentrated in
  ~30 auditable fallback lowerings at a single "equivalency point."
  Self-application (round-tripping the compiler's own artifacts) is the
  honesty test.
- **Type inference ↔ soft/gradual typing** (Cartwright–Fagan; Siek–Taha).
  Inference that never rejects, aimed at cross-language fidelity rather than
  checking; unknowns are inert by policy, which allowed a provably
  behavior-neutral landing under the fixpoint.
- **Documentation dialect ↔ literate programming and doctests** (Knuth;
  doctest). Articles are programs whose compilation *executes* the demo and
  gates publication on drift between claimed and captured output — doctest's
  idea promoted to the article level, implemented as an ordinary dialect.
- **LLM seam ↔ LLM-integrated tooling.** The 2025 design had the LLM in the
  execution path; the shipped system demoted it to a reserved pipeline stage
  plus a development methodology (probe → LLM-infer → human-proof → capture
  as test → replace with rules). As a case study, the direction of that
  displacement — from mechanism to methodology — is itself a finding.

## 3. What is genuinely novel

An honest ranking, most to least distinctive, for the paper's claims:

1. **The combination as a system.** No single relative combines: one open
   element algebra from characters to programs; data-driven classification
   over a fixed shape grammar; fixpoint lowering written in the language;
   sideways-inheritance packaging of every concern; and a byte-exact
   self-hosting proof underwriting extension. The architecture's parts are
   each traceable; the *closure* of the parts over themselves (grammar
   declared in the dialect, generators lowered by the lowering system,
   plugins verified by the fixpoint) is the novelty.
2. **Classification decoupled from parsing as the universal rule**, not an
   escape hatch — including the longest-keyword-subsequence verb dispatch
   and soft failure with coverage telemetry as the language-development
   loop.
3. **Fallback lowering after full inference, by whole-program re-emission
   to a byte-stable fixpoint**, with atomicity as an emergent property and
   the compiler's own metaconstructs among the composites.
4. **The fixpoint/oracle verification pair** as an explicit substitute for
   static guarantees, including behavior-neutral landings of new analyses.
5. **The element-order contract** (derive post-order from the winning tree;
   forward/reverse = bottom-up/top-down) as the single traversal spine for
   all sixteen inferences and the soundness condition for memoized parsing.
6. **Same-position memo invalidation** in Warth-style seed growth, and
   object-identity replay.
7. Characters-as-objects, dialects, sideways inheritance individually — each
   has close relatives; their value here is that they are the *same*
   mechanism reused at every level.

## 4. The trade-off ledger

For the paper's threats-to-validity / discussion section:

| purchased | paid |
|---|---|
| one extension mechanism from lexer to backend | orders-of-magnitude compile-time cost (object-per-character; full re-inference per fallback pass) |
| open construct inventory; no parser changes ever | no static exhaustiveness; misses surface as runtime `debug;`/`error` during builds |
| readable intermediates at every stage | text as the only interchange (re-parse per stage) |
| idiomatic five-language output, byte-identical behavior | backends are deliberately partial (contract + loud failure) |
| provable self-compilation stability | fixpoint proves stability, not correctness — oracles must carry behavior |
| dialect-layered universal translation | per-source-language dialect + lowering work; the long tail is explicit (status lists) |
| plugins verified by the kernel's fixpoint | recompile-to-extend; no runtime loading |

The through-line: **gal3 systematically converts static, per-formalism
guarantees into empirical, whole-system observations** (fixpoint diffs,
oracle bytes, coverage reports, loud failures) — and converts per-phase
machinery into one object algebra. Whether that trade is right depends on
the goal, and for a research vehicle whose language changes weekly and whose
ambition is N×M translation, the five-backends-in-two-days and
Python-round-trip results are the empirical argument that it is.
