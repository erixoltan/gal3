# `include` and the plugin build — design

*Status: design phase, no code yet. 2026-07-13. Companion to the Documentation
dialect work (generalabstractlanguage.com/docs/documentation_dialect.md).*

## Goal and principles

A plugin is gal source, nothing else. Composition happens by inclusion at the
gal (gal-to-gal) stage, so the mechanism is target-language-independent: it
works identically when the compiler binaries are Python, JavaScript, or C++.
All include statements are compiled out by the gal stage; fallback and the
target generators only ever see one monolithic text — functionally the same
position `#include` occupies in C after preprocessing.

This deliberately rejects runtime plugin loading (exec/import), which only
dynamic host languages can offer. The price is a recompile step; the reward is
that the extended compiler is ordinary gal source and inherits the strongest
verification the project has: the self-hosting fixpoint.

## The `include` statement

    include 'file.txt';

- **gal-stage only.** Implemented as an Include inference that runs FIRST,
  before every other inference.
- **Parse-time element splice.** The inference tokenizes and parses the
  included file and splices its elements into the including program's element
  list in place of the statement. Only then do attributes / structure /
  data-type inference run — over the merged tree. This preserves exact
  equivalence with concatenation (`cat`), which everything built so far
  assumes: cross-file inference sees the whole program, and nothing depends on
  gal-stage normalization being idempotent.
- **Recursion.** Spliced elements are scanned for further includes (worklist
  until none remain), all within one compiler instance.
- **Duplicates are errors**, identified by canonical resolved path (realpath),
  not the literal string. A cycle is caught by the same rule but reported as
  "include cycle" — the user's fix is different.
- **Top-level (module scope) only.** An include inside a class or method body
  is a mixin feature wearing an include costume; error in v1.
- **Path resolution**: relative to the *including file's* directory (never the
  CWD), then a plugin search path (e.g. `~/.gal3/dialects/`). Deterministic —
  same input tree, same merged output, always.
- **Provenance**: the inference emits boundary comments
  (`comment 'BEGIN include x.txt';` / `END`) so downstream line numbers in the
  merged file can be traced back to their source files.
- **Downstream tombstones**: the statement is declared in the shared dialect,
  and its fallback/target generators contain only
  `error 'include must be compiled out by the gal stage';`. A leaked include
  then fails with a one-line diagnosis instead of the unclassified-verb
  zdebug hang.

### gal2's include, as reference

`gal2/src/Language.gal:731` declares it; `gal2/src/Goalspell.gal:1396`
implements it as a generation-time splice: `readall` the file's raw text and
emit it as the generated code. Consequences: the included text is parsed only
by the NEXT stage, nested includes leak downstream, duplicates cannot be
detected, and the current stage's classification never sees the content.
The gal3 design moves the splice to parse time specifically to fix all four.

## Vocabulary staging — why the name `include` is safe to reuse

gal2 has a live `include` keyword (`Goalspell.gal:197`), and the gal3 sources
are compiled by gal2 in `./build`. The conflict only bites if gal2 ever
compiles a **bare** include statement. It never needs to:

- The gal3 declaration (`statement Include 'include' …`) and registry entry
  mention the keyword only inside quoted strings, which are opaque to gal2.
- Kernel sources (everything `./build` compiles) contain no include usage —
  that is a standing rule, enforced by the staging below.
- Only manifests and user programs use bare includes, and those are compiled
  by gal3 binaries.

Note: a statement name "unknown to gal2" would buy no safety anyway — unknown
verbs are not ignored, they go unclassified (in practice: the zdebug hang).
Discipline about *where* bare includes may appear is the actual protection,
and with that discipline the natural name is free.

Official include-capable toolchain: the `_3` artifact set (firmly gal3-built).
The gal2-built `gal.py` will contain the inference too and should work, but
support is only claimed for `_3` and later. (Corollary: user-facing tools —
`bin/galdoc`, the oracles — should migrate from `gal.py` to the `_3` set.)

## Build staging

`build` / `selfbuild` / `selfself` stay exactly as they are — concatenation
only, no plugins, frozen. They are the kernel bootstrap and the stability
oracle, and the byte-identical `_3 ≡ _33` signal must stay pure.

Plugins enter through a NEW fourth script — `extend`:

1. Uses the `_3` binaries.
2. Composes each artifact as today (kernel layers, concatenated), and injects
   one line after the code layers and before the artifact's `*_main` layer:

       include 'plugins.txt';

3. `plugins.txt` is the manifest: a gal file that is nothing but include
   statements naming each plugin, in order. (The injected line is itself an
   include, so the manifest is ordinary source; the Include inference resolves
   the rest.)
4. Compiles through the normal chain: the gal stage merges everything and
   compiles the includes out; fallback and the targets see one monolithic
   text. Output: an extended artifact set, kept distinct from the kernel set
   (naming open — see questions).

### Verification (runs on every extend)

- **Extended fixpoint**: the extended compiler recompiles the same
  kernel-plus-manifest input; the second generation must be byte-identical.
  The self-hosting proof extends automatically to every plugin ever written.
- **Empty-manifest identity**: `extend` with an empty `plugins.txt` must
  produce artifacts byte-identical to the kernel `_33` set. This proves the
  include machinery itself changes nothing — the migration acceptance test.
- **Oracles**: five-languages oracle, plus each plugin's own oracle (for the
  Documentation dialect: the hello pilot article must regenerate byte-identical
  markdown and script output).

## Plugin file format

One self-contained gal source file per plugin:

- element declarations (`statement` / `operation` / `syntax`),
- a dialect registry block (`dialect X Compiler { … }` — selection via
  `speaking` is a separate, composing design thread),
- lowerings and any per-target generators,
- `class set` extensions of kernel classes as needed — plugins are full-power
  gal source; because the manifest is included after all kernel layers,
  class-set ordering is guaranteed.

The same plugin file is included identically into EVERY artifact. That is safe
because pass-specific generate bodies become methods on element classes and
are simply never invoked in artifacts that don't run that pass — dead weight,
not errors. Declarations are harmless everywhere.

**Required machinery change**: today `generator Fallback Gal { … }` is a
singleton — a second block generates a second driver class that shadows the
first. Plugins need an extension form (working name: `generator extend
Fallback Gal { generate … }`) that emits only the element-class method
attachments and no driver class. Same for other passes. This is a contained
change to `Statement_Generator`'s codegen.

Convention (v1): plugin files include nothing themselves; the manifest lists
every layer, once, in order. This sidesteps the diamond-dependency problem
(two plugins sharing a helper file would trip the duplicate error). Revisit
with `include once` semantics only if real plugins hit it.

## Open questions

- Naming of the extended artifact set (`gal_x.py`? a `~/.gal3/custom/` dir?
  release names that galdoc and the oracles point at?).
- `speaking` (syntax and block-statement forms) and the dialect-ancestry
  naming fix — designed separately, composes with this: include gets the
  vocabulary into the compiler, `speaking` selects it at classification time.
- Migrating the kernel build scripts themselves from bash `append` to include
  manifests — possible later, gated on the empty-manifest identity test, and
  never for `./build` (gal2 must keep seeing pure concatenation).
- First real plugin: move the Documentation dialect out of the kernel
  (`compiler_dialect.txt` / `fallback_inference.txt` / `python_inference.txt`)
  into `documentation_plugin.txt`, with the hello pilot as its oracle.
