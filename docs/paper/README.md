# gal3 compiler design documentation (paper basis)

A detailed technical description of the gal3 compiler — how it actually
works, with `file:line` evidence — written as the basis for a paper comparing
its architecture to conventional compiler and transpiler design theory.
Written 2026-07-16 from the sources at that date (post-3.0.1, five backends,
Python toolchain, plugin system).

Each chapter documents one mechanism, then closes with a **conventional
theory comparison** table and framing points for the paper. Chapter 13 takes
the whole-architecture view.

| chapter | file | subject |
|---|---|---|
| 1 | [01_overview.md](01_overview.md) | thesis, the pipeline, all innovations in brief, honest costs |
| 2 | [02_characters_and_tokens.md](02_characters_and_tokens.md) | characters/tokens as first-class objects; lexing as object protocol |
| 3 | [03_parsing_and_classification.md](03_parsing_and_classification.md) | shape grammar; packrat + left recursion; dialect classification; element-order contract |
| 4 | [04_inference_pipeline.md](04_inference_pipeline.md) | the sixteen inferences; per-class dispatch; scope as element behavior |
| 5 | [05_fallback_lowering.md](05_fallback_lowering.md) | composite → atomic by re-emission to fixpoint; skycoding |
| 6 | [06_sideways_inheritance.md](06_sideways_inheritance.md) | `class set`; the splice; the sugar family (`generate`/`handle`/`generator`) |
| 7 | [07_dialects.md](07_dialects.md) | declarations → classes; the dialect registry; the declared grammar; coverage-driven development |
| 8 | [08_backends_and_atomics.md](08_backends_and_atomics.md) | the atomic contract (143/59/34); five-language mirror; escaping, precedence, imports; fail-loudly |
| 9 | [09_bootstrap_lineage.md](09_bootstrap_lineage.md) | gal0 (Raku) → gal1 → gal2 → gal3; fixpoint protocol; timeline; the plan that wasn't built |
| 10 | [10_type_inference.md](10_type_inference.md) | Data_Type / Usage; declarative typing; five consumers |
| 11 | [11_universal_translation.md](11_universal_translation.md) | peg, pylex, pyparse, pygen, pygal; the Python dialect; round-trip oracles |
| 12 | [12_plugins.md](12_plugins.md) | the include mechanism; `plugs`; the Documentation dialect; the LLM seam |
| 13 | [13_theory_comparison.md](13_theory_comparison.md) | systematic compare/contrast; novelty ranking; trade-off ledger |

Companion documents elsewhere in `docs/`: [architecture.md](../architecture.md)
(current-state reference), [status.md](../status.md) (done/open),
[data_type_inference.md](../data_type_inference.md),
[five_languages.md](../five_languages.md),
[peg_python_parsing_design.md](../peg_python_parsing_design.md),
[include_plugin_design.md](../include_plugin_design.md), and
[history/](../history/) (the original April-2025 vision, kept as a record).
