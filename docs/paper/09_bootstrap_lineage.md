# The bootstrap lineage: gal0 → gal1 → gal2 → gal3

*Chapter 9 of the gal3 compiler design documentation. Sources: `gal1/`
(incl. `bootstrap.raku`), `gal2/gsbuild`, `gal3/build`/`selfbuild`/`selfself`,
repo-root `fullbuild`, `docs/history/`,
`goalspell_compiler_review_erik_latest_responses.md`.*

## Four generations

| generation | written in | compiled by | survives today as |
|---|---|---|---|
| **gal0** (2021) | Raku, hand-written (`gal1/bootstrap.raku`, ~8.5k lines) | rakudo (interpreted) | still executed at the root of every `fullbuild` |
| **gal1** (2021) | gal, prefix ("verb-first") syntax, `.gal` files in `gal1/compiler/src/` | gal0 bootstraps it into Raku; it then self-compiles to Python and JavaScript | its Python build (`~/.gal/gal_compiler.re.py`) is the compiler that builds gal2 |
| **gal2 / goalspell** (2022) | gal1 syntax (`gal2/src/*.gal`), *producing* the flexible keyword-based goalspell (`.gs`) surface syntax | gal1's Python compiler | installed at `~/.goalspell/goalspell`; sole remaining job is bootstrapping gal3 |
| **gal3** (2024-10 → ) | gal3 syntax, `.txt` files in `gal3/` | gal2 for the bootstrap pass; then **itself** — self-hosting fixpoint since 2026-06-10 | the current compiler: 13 self-hosting artifacts, 5 complete targets |

Each generation is written in the language of the previous one — the classic
bootstrap ladder, except that **every rung is preserved and still runs**. The
repo-root `fullbuild` script replays the entire 2021→2026 ancestry in one
command:

1. **gal1**: `gal1/compiler/legacy.sh` — rakudo runs the 2021 `bootstrap.raku`
   (gal0) over `src/*.gal`, producing the Raku gal1 compiler; then that
   compiler cross-builds itself to Python and JavaScript, and the three
   outputs are diffed against each other ("The three compilers must produce
   identical atomic and compiled code" — `gal1/README.md`). This three-way
   diff is the gal1-era ancestor of gal3's fixpoint check. `rebuild.sh`
   publishes `gal_compiler.re.py` into `gal2/bin/`.
2. **gal2**: `gal2/gsbuild` — gal1's Python compiler concatenates ~30 `.gal`
   modules and runs them through `gal → fallback → atomic → python`,
   installing `~/.goalspell/goalspell`. Note: **the gs → fallback → atomic →
   target pipeline predates gal3** — it is gal2's architecture, inherited and
   generalized.
3. **gal3**: `gal3/build` — gal2 compiles the gal3 `.txt` sources.

A naming note for the paper: contemporaneous gal1-era documents call the Raku
program simply "the gal bootstrap compiler"; the retrospective numbering
gal0/1/2/3 appears in later documents (`ideas.md`,
`goalspell_compiler_review_erik_latest_responses.md`, `docs/architecture.md`).
Erik's own summary of the ladder (from the review-responses doc):

> gal0 was implemented in Raku and contains many obsolete ideas. It compiles
> into raku. — gal1 is written in gal0. It has a prefix-oriented syntax,
> meaning that the first element in a statement, operation or syntax is always
> the verb. — gal2 is written in gal1. So it is written in a prefix-oriented
> syntax but it produces a more flexible keyword-based dialect-resolved
> syntax. — gal3 will be written in gal2.

## Syntax evolution in one example

The same loop — "iterate my arguments, appending the gal of each" — across
generations:

**gal1** (verb-first everywhere; even assignment is a verb):

```
    string Code '';
    entity Arg;
    foreach [my Arguments] Arg
    {
        append Code ' ' [. Arg Gal];
    }
    i= Code;
```

**gal2 / goalspell** (keyword position is flexible, dialect-resolved):

```
    string Code '';
    object Arg;
    for each Arg in [my Arguments]
    {
        Code s+ ' ' [Arg.Gal];
    }
    i = Code;
```

gal3 keeps goalspell's shape with a maturing standard vocabulary (`say` for
`writeline`, `my Balance = ...` for `my= Balance ...`, `class`/`property`/
`constructor` declarations as in `examples/bank.txt`). Constant across all
four generations: the statement / `(operation)` / `[syntax]` / `{block}`
element taxonomy, whitespace separation, interchangeable quote styles, and the
case convention (lowercase keywords, Uppercase/`_`/`$` names — *enforced* by
gal0–2, a convention in gal3).

The gal1→gal2 step is the pivotal design move for this paper: gal1's grammar
fixed the verb at position zero (an s-expression discipline); gal2 let the
verb float and be *found* by dictionary lookup — the birth of the
dialect-resolved classification that gal3 generalizes (chapter 3).

## The fixpoint protocol

gal3's self-hosting proof is a three-script protocol:

```bash
./build       # gal2 compiles the .txt sources        → ~/.gal3/{artifact}.py
./selfbuild   # those binaries recompile the sources  → ~/.gal3/{artifact}_3.py
./selfself    # the _3 binaries rebuild once more     → ~/.gal3/{artifact}_33.py
```

Self-hosting holds when `_3` ≡ `_33` **byte-for-byte** for all thirteen
artifacts (`gal fallback galpy galjs galgo galjava galcpp galc peg pylex
pyparse pygen pygal`). Once the fixpoint is reached, gal2's presence in the
chain provably cannot change the output — "gal2 is now purely a bootstrap
step" (`docs/status.md`). Since 3.0.1 (2026-07-01) JavaScript is a second
self-hosting target alongside Python.

Two properties of this discipline are worth stating precisely:

- **The fixpoint is structural, not behavioral.** Byte-identity between
  generations proves the compiler is *stable under self-compilation* — it
  catches any change that doesn't survive being compiled by itself. It does
  **not** prove correctness: two consistently-wrong generations diff clean.
  Behavior is checked separately by output **oracles** (`bin/five_oracle.sh`
  compares five programs × five targets against ground truth, 26 green cells;
  the Python toolchain has its own byte-level oracles against CPython).
  Fixpoint + oracle together substitute for the static guarantees the
  architecture gave up (chapter 4).
- **The fixpoint doubles as a regression harness.** Because the compiler is
  the largest gal program in existence, "does the fixpoint still hold?" is a
  free, total test over the entire language surface after any change. Several
  features (e.g. data-type inference) were explicitly required to be
  *behavior-neutral under the fixpoint* when introduced.

## Timeline

| date | milestone |
|---|---|
| 2021 | gal0 (Raku) + gal1; gal1 self-builds into Raku, Python, JavaScript with three-way diff |
| 2022 | gal2/goalspell era: gs syntax, fallback→atomic pipeline, Python/JS/Raku (+MUMPS, HTML) targets |
| 2024-10-12 | gal3 begins ("new gal3") |
| 2025-04 | original LLM-centric plan's deadline; "gal3 finished major checkin" — but the grind continues |
| 2025-09 | first self-build attempts |
| 2025-10-13 | "gal3 arguments breakthrough" |
| 2026-01-16 | sideways inheritance lands |
| **2026-06-10** | **3.0.0 — self-hosting fixpoint**, all artifacts byte-identical |
| 2026-07-01 | 3.0.1 — galjs second self-hosting target |
| 2026-07-03→06 | Python-parsing initiative: peg, pylex, pyparse, pygen, pygal |
| 2026-07-06 | data-type inference ported gal2→gal3, behavior-neutral |
| 2026-07-11→12 | Go, Java, C++ backends; five-languages oracle green (26 cells) |
| 2026-07-14→15 | `include` statement and the plugin system |

(Two dated claims rest on docs rather than commits: the exact 2026-06-10
fixpoint date, and everything pre-2024 — the monorepo's git history begins
2024-09-12; the earlier era is evidenced by in-tree 2021/2022 copyrights and
READMEs.)

## The plan that wasn't built

`docs/history/` preserves the April-2025 vision with an explicit disclaimer:
it described an **LLM-centric** compiler — every inference implemented via LLM
reasoning, a JSON protocol for inference results, API and local models, an
`english "..."` statement in place of code. What shipped inverts that:

- All seven then-missing inferences were implemented as **rule-based code**;
  `Infer_Intelligence` survives as a dormant seam (chapter 4).
- Correctness discipline came from the **fixpoint + oracles**, which appear
  nowhere in the 2025 plan.
- Target breadth *exceeded* the plan (five languages vs. planned two), and the
  unplanned Python-ingestion toolchain (chapter 10) became the front half of
  the universal-translator goal.
- The LLM idea survived as *methodology*, not architecture: probe →
  LLM-infer → human-proof → capture as test → replace with fast code
  (`docs/inference_process.txt`), realized concretely in data-type inference.

This divergence is itself a finding for the paper: the LLM-in-the-loop
compiler was designed first and *displaced* by a deterministic self-hosting
discipline — with the LLM demoted from execution path to development process.

## Conventional theory comparison

| aspect | classical bootstrapping | gal |
|---|---|---|
| ladder | T-diagrams; each generation compiles the next; old rungs typically discarded | four generations, every rung preserved and re-runnable from source in one command |
| fixpoint | "compiler compiles itself" (e.g. Pascal P4, early C); rarely checked byte-exactly | byte-identity across 13 artifacts, three generations deep (`build`/`selfbuild`/`selfself`) |
| trusting trust | Thompson's attack: binary-only ancestry hides trojans; Wheeler's Diverse Double-Compiling as the countermeasure | the full ancestry back to an interpreted 2021 Raku script is source-replayable — a DDC-friendly lineage (rakudo, CPython, node as independent roots) |
| self-hosting motive | performance + dogfooding | dogfooding as *test harness*: the compiler is the language's biggest program, and the fixpoint is a total regression check |
| verification | compiler test suites; CompCert-style proof at the far end | structural fixpoint (stability) + behavioral oracles (correctness), explicitly separated |

Framing point for the paper: the interesting theoretical object here is the
**pair** (fixpoint, oracle). Classical self-hosting folklore treats "it
compiles itself" as the milestone; gal3's discipline makes explicit that
self-compilation stability and behavioral correctness are orthogonal, and
institutionalizes one mechanism for each.
