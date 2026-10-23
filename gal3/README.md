# gal3 compiler

The gal3 compiler — the third generation of **gal** (*general abstract
language*). gal3 self-hosts (its compiler is a gal program that compiles itself
to a byte-identical fixpoint) and generates six target languages: Python,
JavaScript, Go, Java, C++ and MUMPS (plus a frozen C proof of concept).

The source files here are `.txt` only so editors stop trying to syntax-highlight
them — they are gal source. See `../docs/architecture.md` for how it all works
and `../docs/status.md` for current state.

## Prerequisites

- Only [`uv`](https://astral.sh/uv): the shared environment at the repo root is
  fetched and activated by sourcing `../galenv` (the build scripts do this
  automatically). Build from the repo root with `../bootstrap.sh` — it seeds
  the frozen stage-0 compiler from `../bootstrap/`, so no prior gal install is
  needed.
- For running generated code in every target: `node`, `go` (user-local at
  `~/.local/go`, added to PATH by `galenv`), a JDK (`javac`/`java`), a C++
  compiler (`g++`), and — for the MUMPS target — YottaDB.

## Build

`../bootstrap.sh` from the repo root establishes the self-hosting fixpoint
(stage-0 builds `_3`, `_3` builds `_33`, all artifacts must be byte-identical).
Inside this directory the three scripts it drives are:

```bash
./build       # the stage-0 compiler in ~/.gal3 compiles the .txt sources → ~/.gal3/{artifact}.py
./selfbuild   # those gal3 binaries recompile the sources → ~/.gal3/{artifact}_3.py
./selfself    # the _3 binaries rebuild once more → ~/.gal3/{artifact}_33.py
```

Self-hosting holds when `_3` and `_33` are byte-identical for every artifact:

```bash
./build && ./selfbuild && python -m py_compile ~/.gal3/*_3.py && ./selfself
for a in gal fallback galpy galjs galgo galjava galcpp galc peg pylex pyparse pygen pygal; do
    diff ~/.gal3/${a}_3.py ~/.gal3/${a}_33.py && echo "$a ok"
done
```

`../fullbuild` runs the whole gal1 → gal2 → gal3 chain from scratch. Fast
per-artifact iteration scripts exist for the Python toolchain: `./pybuild`,
`./pegbuild`, `./pyparsebuild`, `./pygenbuild`, `./pygalbuild`.

## Compile and run a program

Every artifact is a plain CLI: `python ~/.gal3/<artifact>.py <input> <output>`.
The pipeline is gal → fallback (repeat to fixpoint) → target:

```bash
python ~/.gal3/gal.py       examples/bank.txt  /tmp/bank.gal
python ~/.gal3/fallback.py  /tmp/bank.gal      /tmp/bank.fb0
python ~/.gal3/fallback.py  /tmp/bank.fb0      /tmp/bank.atomic   # repeat until stable
python ~/.gal3/galpy.py     /tmp/bank.atomic   /tmp/bank.py
PYTHONPATH=$HOME/.gal3 python /tmp/bank.py
```

Swap `galpy.py` for `galjs.py`, `galgo.py`, `galjava.py`, `galcpp.py` or
`galmumps.py` to emit the other targets. The oracle `bin/five_oracle.sh` does
exactly this across five programs and six languages and checks the outputs
are byte-identical.

## Layout

- `*_inference.txt` / `*_main.txt` — per-target backends (python, javascript,
  go, java, cpp, c) and their entry points.
- `compiler_base.txt`, `compiler_dialect.txt`, `gal_base.txt`,
  `fallback_inference.txt` — the compiler core, dialect, gal front end, and
  fallback lowering.
- `attributes_inference.txt`, `structure_inference.txt`,
  `data_type_inference.txt`, `llm_inference.txt` — inference stages in the shared
  "zero" stack.
- `peg_*`, `py_*`, `pyparse_*`, `pygen_*`, `pygal_*` — the external-Python
  toolchain (grammar → parser, tokenizer, parser, normalized regeneration,
  Python → gal).
- `bin/` — runtime (`Runtime.py`), debugger (`zdebug.py`), and the oracle
  scripts (`five_oracle.sh`, `pylex_oracle.py`, `pygen_oracle.py`,
  `pygal_oracle.py`, …).
- `examples/` — sample programs, including the five-languages set
  (`example.txt`, `fizzbuzz.txt`, `bank.txt`, `receipt.txt`, `checkout.txt`).
- `grammars/` — `python-3.11.gram` and `tiny.gram`.

## Debugging

You debug in the target language. Run the generated Python under `zdebug`
(installed to `~/.gal3/zdebug.py`), or `import` a compiled artifact as a module
and introspect its element tree. A `debug;` statement lowers to a
`zdebug.zbreak()` breakpoint; because that can swallow errors during an
unattended build, temporarily stub `~/.gal3/zdebug.py` with a no-op `zbreak` to
see the real failure, then restore it. See `CLAUDE.md` for the working recipes.
