# Python environment strategy for the gal toolchain

The gal toolchain (gal1, gal2, gal3) all run on Python. Historically every build
script invoked a bare `python` / `python3`, assuming one global interpreter with
one global set of packages. That assumption is now broken:

- Distro Python is "externally managed" (PEP 668): `pip install` is refused.
- Different gal versions accumulated different dependency sets.
- Two half-applied approaches were in the tree (pyenv `setup_venv.sh`, plus a
  stray `uv init` scaffold in `gal3/`).

## The approach: one uv-managed venv at the repo root

There is a single virtual environment for the entire toolchain, defined by:

| File                 | Role                                                        |
|----------------------|-------------------------------------------------------------|
| `pyproject.toml`     | The union of real dependencies (core + optional groups).    |
| `uv.lock`            | Pinned, reproducible resolution. Commit this.               |
| `.python-version`    | Pins the interpreter (3.14). uv downloads it; distro is untouched. |
| `.venv/`             | The environment itself. Git-ignored; recreated by `uv sync`.|
| `galenv`             | Sourced by every build script to activate the venv.         |

`uv` is the only prerequisite. It is a single static binary that fetches its own
Python, so the host distro's python and pip are never touched — that is what
makes builds reproducible across machines and immune to PEP 668.

### How build scripts use it

Each entry script sources `galenv` on its first lines:

```bash
source "$(dirname "$(readlink -f "$0")")/../galenv" || exit 1   # depth varies
```

`galenv` runs `uv sync` (near-instant when already current), then prepends
`.venv/bin` to `PATH`. Because the venv is on `PATH`, every existing bare
`python` / `python3` call resolves to the locked interpreter with no further
edits. The activation is exported, so child build scripts inherit it and skip
re-syncing (guarded by `GAL_ENV_READY`).

Wired into: `fullbuild`, `startup`, `gal1/compiler/{legacy,rebuild}.sh`,
`gal2/gsbuild`, `gal3/{build,selfbuild,selfself,run_compiler.sh}`.

## Setting up a new machine

```bash
# 1. Install uv once (single static binary):
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. From the toolchain root, create the environment (also fetches Python 3.14):
cd ~/code/gal && uv sync

# 3. Build as usual — galenv keeps the venv in sync automatically:
./fullbuild
```

## Dependencies

Core (needed even to build gal3, whose Runtime/compiler import them at module
top): `requests`, `openai`, `bcrypt`, `ollama`, `markdown`, `mcp`, `pyyaml`.

Optional groups, not installed by a plain `uv sync`:

- `audio` — `google-cloud-texttospeech`  → `uv sync --group audio`
- `dev`   — `pytest`, `pytest-cov`, `black`, `isort`, `ipython`

`sqlite3-api` from the old `requirements.txt` was dropped: `sqlite3` is stdlib.

## Running the installed compilers (gal, galpy, fallback)

`./build` installs the compilers into `~/.gal3` (`gal.py`, `galpy.py`,
`fallback.py`, and the `_3`/`_33` self-built variants). Running them with a bare
`python` fails — they import `yaml`, `Runtime`, etc., which only exist in the
shared venv. You do **not** need to activate the venv to run them: a venv's own
`python` binary already carries the full environment.

`bin/galrun` is a launcher that does exactly that, and `bin/{gal,galpy,fallback}`
are symlinks to it. The link name selects the program; arguments pass straight
through:

```bash
galpy source.gal target.py     # = ~/code/gal/.venv/bin/python ~/.gal3/galpy.py source.gal target.py
gal   source.tx2 target.gal
fallback in.gal out.fallback
```

The launcher resolves the venv relative to itself (so it is cwd-independent) and
recreates the venv via `galenv` if it is missing. Put `bin/` on `PATH`:

```bash
export PATH="$HOME/code/gal/bin:$PATH"      # or re-run ./install
```

To add another command, symlink it to `galrun` and add a case entry in
`bin/galrun`.

## Changing dependencies

Edit `pyproject.toml` (or `uv add <pkg>`), then `uv sync`. Commit both
`pyproject.toml` and `uv.lock`. The next build picks it up automatically.
