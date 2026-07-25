# gal3 Documentation

Reference documentation for the gal3 compiler. Start with **architecture** and
**status**; the rest are deep dives on specific initiatives.

## Start here

- **[architecture.md](architecture.md)** — how the compiler works today: the
  `gal → fallback → atomic → target` pipeline, the inference stages, dialects,
  the fourteen self-hosting artifacts, the build chain, how self-hosting is
  proven, and the four languages the compiler itself runs in. *Read this
  first.*
- **[status.md](status.md)** — what is done, in progress, and open, with dates
  and pointers.

## Initiative deep dives (current)

- **[five_languages.md](five_languages.md)** — the five sample programs compiled
  to six target languages with byte-identical output; the 31-cell oracle; the
  article / book chapter / video plan.
- **[data_type_inference.md](data_type_inference.md)** — how gal infers data
  types and lets each backend impose its own typing (the `say` → `printf` case,
  string-in-numeric conversions across five type systems).
- **[js_selfhost_design.md](js_selfhost_design.md)**,
  **[java_selfhost_design.md](java_selfhost_design.md)**,
  **[mumps_design.md](mumps_design.md)** — hosting the compiler in another
  language: what each host forced gal to answer, the gates (`jsself`,
  `javaself`, `mumpsself`), and the semantic gaps each one exposed. MUMPS is
  the furthest from Python and the most instructive: no objects, one data
  structure, and an empty string where None should be.
- **[peg_python_parsing_design.md](peg_python_parsing_design.md)** — parsing
  external Python (and pegen grammars) into gal elements: the `peg` / `pylex` /
  `pyparse` / `pygen` / `pygal` toolchain, the element-order contract,
  memoization, and left-recursion.

## Design notes (historical / methodology)

These predate self-hosting and are kept as design context, not current spec:

- `inference_process.txt` — the probe → LLM-infer → proof → capture-as-test-case
  methodology (realized concretely in data type inference).
- `structure_inference.txt`, `structure_inference_test.txt` — early notes on the
  structure inference stage.
- `language_ref/gal3_language_reference.md` — a language reference that predates
  self-hosting; useful but uses some non-current examples. Due for a refresh
  (see status.md).
- `venv.md` — Python virtual-environment / toolchain setup notes.
