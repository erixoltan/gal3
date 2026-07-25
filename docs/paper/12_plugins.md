# Plugins, the include mechanism, and the LLM seam

*Chapter 12 of the gal3 compiler design documentation. Sources:
`docs/include_plugin_design.md`, `gal3/plugs` (the plugin build script),
`gal3/gal_compiler_plugins.txt` (the manifest), `gal3/Documentation.gal`,
`gal3/llm_inference.txt`, `docs/inference_process.txt`, `gal3/synthesis.txt`.*

## The design stance

> "A plugin is gal source, nothing else. Composition happens by inclusion at
> the gal (gal-to-gal) stage, so the mechanism is target-language-
> independent: it works identically when the compiler binaries are Python,
> JavaScript, or C++. … This deliberately rejects runtime plugin loading
> (exec/import), which only dynamic host languages can offer. The price is a
> recompile step; the reward is that the extended compiler is ordinary gal
> source and inherits the strongest verification the project has: the
> self-hosting fixpoint." — `docs/include_plugin_design.md`

A gal3 plugin is a bare list of gal statements — new element classes, new
`statement`/`operation`/`syntax` declarations, `dialect` blocks, `class set`
grafts onto kernel classes — spliced textually into `module Compiler` and
compiled into a new compiler binary. The extension surface is the *entire
language*, because the compiler is a gal program.

## The include mechanism: staged splicing

`include "Name";` is a kernel dialect statement resolved **only in the gal
stage**: its generator (`gal_base.txt:517`) reads `Name.gal` and emits that
file's text in place of the statement. Termination of nesting is a
*build-staging invariant*, not a worklist:

> "an included file is the output of a previous gal-stage compilation, whose
> own include statements were resolved when it was built, so includes can
> never recurse … a .gal file must never contain an include statement."

Only pre-compiled `.gal` files (include-free by construction) are includable.
Every failure mode is loud: a missing file or unquoted name errors; a failed
include **aborts the build** ("without this check a silently truncated
program would be written as if it succeeded," `gal_base.txt:640`); and the
fallback stage carries a tombstone — an `include` reaching fallback means the
file wasn't produced by the gal compiler, and it refuses.

## The build path: `plugs` and kernel purity

The kernel scripts (`build`/`selfbuild`/`selfself`) remain pure
concatenation — no plugins, frozen. Extension lives in a fourth script,
`plugs`, which:

1. compiles each plugin source to its include-free `.gal` form using the
   **`_33` binaries** — the doubly self-hosted fixpoint kernel (the
   Documentation dialect's source lives in the website repo and is compiled
   first);
2. compiles the **manifest** (`gal_compiler_plugins.txt`, ten lines: a
   flowerbox + `include "Documentation";`) to `gal_compiler_plugins.gal` —
   verified to be a verbatim splice of the plugin text;
3. rebuilds the artifact set with an `add_include` step injecting
   `include "gal_compiler_plugins";` (wrapped in BEGIN/END provenance
   comments) between the code layers and each artifact's main layer,
   producing a parallel `*_plug.py` artifact set (14 artifacts).

So the extended compiler is: fixpoint kernel + textual splice + the same
gal→fallback→target pipeline — and the self-hosting proof underwrites it.
Two `_plug` artifacts currently receive the include: `gal_plug` (the extended
front end) and `galdoc_plug` (a dedicated tool whose main selects
`Dialect_Documentation`). Dialect selection is per-tool, by property
assignment: `C.Dialect = (new Dialect_Documentation);`.

## The first real plugin: the Documentation dialect

The proof-of-concept plugin is a dialect for **writing articles about gal as
gal programs**. From its header:

> "the compiler parses the article, RUNS its demo session for real (file
> statements write files, bash statements run through a shell, and the
> captured output is the only output ever published), and infers the
> markdown article and the booktok video script directly on the element
> tree … stated expectations are diffed against reality and drift is
> reported per element."

It declares eleven statements (`chapter`, `section`, `paragraph`/`para`/`p`,
`aside`, `brand`, `diagram`, `file`, `file from`, `show`/`edit`/`vim`,
`bash`, `bash expect`) over three behavioral classes (`Heading_Statement`,
`Body_Statement`, `Runtime_Statement`), plus a `dialect Documentation`
registry block. Multi-word verbs (`bash expect`, `file from`) use gal's
ordinary multi-word classification — no new syntax classes needed. Every
statement carries its own `Markdown` and `Script` properties, computed
bottom-up by `Infer_Markdown`/`Infer_Script` after `Doc_Execute` has captured
reality — the same element-tree, post-order, per-class-inference pattern as
the compiler itself, aimed at prose.

The payoff is a testing regime for documentation: `bash expect` diffs stated
output against captured output (`PASS`/`DRIFT` per element), the `galdoc`
wrapper exits nonzero on any drift ("compiler bug or stale article"), and
**every published article is thereby a regression test against the current
compiler**. Downstream, the emitted `script.md` (with `<!-- vid: ... -->`
annotations) flows through `galvid` into the booktok storyboard/video
pipeline — an article is one gal program that becomes a demo session, a
markdown article, and a video script.

(An `svg_dialect.txt` exists as a one-line stub — a declared intention for a
diagram dialect, zero implementation. The `.elems` sidecar files seen beside
plugin compiles are element-tree reports — the per-element, per-stage dump
every artifact writes, and the "probe" artifact of the LLM methodology
below.)

## The LLM seam

`llm_inference.txt` is 17 lines and structurally *itself a sideways
extension* — `class append Element` grafting `Infer_Intelligence` onto the
universal element class, concatenated into the zero stack of every artifact.
Its active body only gathers context (the element's source text and
stage-annotated report); the model call —
`string Response (llm compile Target_Language Input Report);` … `my Python =
Response;` — is commented out, as is the pipeline stage (#16) that would
invoke it. The compiler self-hosts and generates all targets rule-based.

The *methodology* is live even though the seam is dormant
(`docs/inference_process.txt`, realized concretely in data-type inference):

1. **Probe** — dump the element list (`.elems`) before the inference.
2. **LLM-infer** — ask a model to infer the property for every element;
   a human proofreads.
3. **Capture** — the proofread result becomes a test case.
4. **Replace** — write rule code per element class ("sideways inheritance,
   every language element class implements an `Infer_Data_Type` method"),
   validated against the captured cases.
5. **Bias** — "we record all LLM decisions as possible test cases. We retain
   test cases based on gratitude. How much do they help us? … We write code
   for what works and it runs faster, and we save the hard things for the
   LLM."

`synthesis.txt` extends this into a design for *generating* new language
elements under a budget/gratitude/cost economics — the generative half of
the loop, with synthesized elements answering the same `Infer_Gal`/
`Infer_Python` surface as everything else. (Older agent experiments —
`shell_agent.txt`, `development_agent.txt`, the `english/` prompt-scripted
compiler modules — survive in the tree as the gal2-era exploration of the
original LLM-centric vision; see chapter 9 for how that vision inverted.)

## Conventional theory comparison

| aspect | conventional design | gal3 |
|---|---|---|
| compiler plugins | host-language APIs against compiler internals (GCC plugins, Clang plugins, Rust proc-macros, GHC plugins); ABI/version fragility | plugins are source in the compiled language; the "API" is the element class hierarchy + dialect declarations |
| loading | dynamic (dlopen/import) at compile time | staged textual inclusion + recompile; works identically under any target-language binary |
| safety story | plugin API stability contracts | the extended compiler re-inherits the fixpoint + oracle verification; failures are loud at build time |
| DSL embedding | macros / external DSLs with separate toolchains | a dialect: same parser, same element machinery, new vocabulary; selected per tool |
| literate programming / doc tests | doctest, mdBook `include`, notebooks | articles are programs whose *compilation executes the demo* and diffs claimed vs. actual output (drift gating) |
| LLM-in-compiler | emerging: LLM-backed copilots outside the compiler | a reserved inference stage inside the pipeline, deliberately demoted to a development methodology (probe→infer→proof→capture→replace) |

Framing points for the paper:

- **The plugin mechanism is the architecture eating itself, on purpose.** It
  composes exactly the primitives earlier chapters describe: dialects for
  vocabulary, `class set` for behavior, fallback for meaning, the fixpoint
  for verification, textual gal for interchange. Nothing new was added to
  the kernel except one statement (`include`) whose entire semantics is
  "splice a file the pipeline already produced."
- **C's preprocessor position, but staged and typed by construction.** The
  design doc's own comparison is apt: includes occupy the position of
  `#include` after preprocessing — but the includable unit is a *compiled
  compiler layer*, not raw text, so nesting terminates by construction and
  failures cannot silently truncate.
- **The Documentation dialect is the strongest evidence for the dialect
  claim** (chapter 7): a non-code domain (technical prose with executable
  demos) expressed as gal statements, parsed by the unchanged shape parser,
  with build-gating semantics — a language workbench result achieved with a
  ten-line manifest.
