# gal — the general abstract language

**LLMs translate code plausibly. gal translates code provably.**

gal is a self-hosting compiler whose architecture makes every translation
*checkable*: rules handle the cases it recognizes, and a mechanical
round-trip — a byte-for-byte fixpoint plus cross-target oracles — proves the
output is faithful rather than merely plausible. The language is the
substrate; **verified translation is the point.**

One gal program compiles to **Python, JavaScript, C++, Go, Java, and MUMPS**,
and the five-languages oracle requires the six outputs to be byte-identical in
behavior. The compiler is written in itself: it rebuilds itself byte-for-byte,
and it also *runs* on four of its own targets (CPython, Node, the JVM, and
YottaDB).

> `gal` is always written lowercase — it stands for *general abstract language*.

## Prove it in one command

The only prerequisite is [`uv`](https://astral.sh/uv) (one static binary; it
fetches the pinned Python itself):

```bash
git clone https://github.com/erixoltan/gal3.git
cd gal3
./bootstrap.sh
```

`bootstrap.sh` uses the checked-in, frozen stage-0 compiler in `bootstrap/`
(no proprietary bootstrap, no prior gal install) to:

1. **selfbuild** — the stage-0 compiler compiles the current sources into a
   fresh compiler (the `_3` set);
2. **selfself** — that fresh compiler compiles the sources *again* (the `_33`
   set);
3. **diff** — every one of the 14 artifacts must be byte-identical between the
   two generations.

If they match, the compiler is a **fixpoint of itself** and you see:

```
FIXPOINT OK — 14 artifacts byte-identical across two self-hosted generations.
```

That equality is the proof: a compiler that reproduces itself exactly, from a
public seed, on your machine.

## The oracles

Two mechanical checks back the fixpoint — they are also the contribution gate
(see [CONTRIBUTING.md](CONTRIBUTING.md)):

```bash
gal3/bin/regress_oracle.sh                       # each case pins a fixed bug
GAL_ORACLE_LANGS=py,js gal3/bin/five_oracle.sh   # cross-target byte-identity
```

The full five-languages oracle (`gal3/bin/five_oracle.sh`, all backends)
requires `g++`, `go`, `javac`, and — for the MUMPS cells — YottaDB.

## Layout

| path | what |
|------|------|
| `gal3/` | the compiler: gal sources (`*.txt`), backends, and the self-hosting scripts |
| `bootstrap/` | the frozen stage-0 compiler (`gal`, `fallback`, `galpy`, `Runtime`) |
| `docs/` | architecture, status, per-feature designs, and the compiler-theory paper |
| `tools/` | `galglobals` (LMDB-backed globals), YottaDB routines, ramdisk helpers |
| `galenv`, `pyproject.toml`, `uv.lock` | the shared uv-managed Python environment |

Start with [`docs/architecture.md`](docs/architecture.md) and
[`gal3/CLAUDE.md`](gal3/CLAUDE.md) for the build-and-fixpoint loop, or
[`docs/paper/`](docs/paper/) for the design in depth.

## License

gal is licensed under the **Apache License, Version 2.0** — see
[LICENSE](LICENSE) and [NOTICE](NOTICE). The patent grant is deliberate:
the engine is meant to be adoptable, forkable, and trustworthy, with no
open-core withholding.

### Trademark

The **code** is Apache-2.0 and anyone may fork it. The **name** *gal* and
**generalabstractlanguage.com** are trademarks of Erik Zoltán. The license
grants rights in the software, not in the marks: you may build on gal and say
your work is *based on* or *compatible with* gal, but please don't use the name
or the domain in a way that implies endorsement or sells confusion about which
project is which. Anyone may fork the code; nobody else may sell the name.

Copyright 2026 Erik Zoltán
