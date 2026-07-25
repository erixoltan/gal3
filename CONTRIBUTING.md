# Contributing to gal

gal's review gate is **mechanical**. The fixpoint and the oracles decide
whether a change is correct — not a maintainer reading diffs. A pull request
that keeps them green is reviewable; one that breaks them is not, regardless of
how it looks. This is deliberate: it lets the project accept work from anyone
(humans and AI assistants alike) without the review load growing with the
contribution volume.

## The gate

Your branch must pass all three of these — they are exactly what CI runs on
every pull request:

```bash
./bootstrap.sh                                   # FIXPOINT OK — 14 artifacts
gal3/bin/regress_oracle.sh                       # every pinned bug still fixed
GAL_ORACLE_LANGS=py,js gal3/bin/five_oracle.sh   # cross-target byte-identity
```

If `bootstrap.sh` does not print `FIXPOINT OK`, the compiler no longer
reproduces itself and the change cannot be merged. See
[README.md](README.md#prove-it-in-one-command) for what the fixpoint means.

## If you fixed a bug, pin it

Any bug fix must come with a new **regression case** so the bug cannot return
silently. Add a tiny program plus its expected output to
`gal3/examples/regress/` and a `check` line in `gal3/bin/regress_oracle.sh`.
A shared inference can break three backends at once; the regress oracle is where
that shows up first, one case at a time. A fix without a pinning case will be
asked to add one before review.

## Good first contributions

The ideal unit of work is **self-contained, mechanically checkable, and
genuinely useful** — which is exactly what a backend is:

- **A new target backend.** Add a `<lang>_inference.txt` + `<lang>_main.txt`
  the way the existing backends do, wire it into `selfbuild`/`selfself` and the
  `five_oracle.sh` matrix, and it passes when its output is byte-identical to
  the other targets for every oracle program. Nothing else needs to trust it.
- **A new regression or oracle case** that pins behavior currently unprotected.
- **A fix to any artifact that breaks the fixpoint or an oracle.**

Language and gal-source conventions live in
[`gal3/CLAUDE.md`](gal3/CLAUDE.md); the architecture is in
[`docs/architecture.md`](docs/architecture.md).

## How the source is laid out

The compiler is gal source in `gal3/*.txt` (the `.txt` extension only stops
editors from mis-highlighting them). Each artifact is assembled from a list of
these fragments — see the `append` lines in `gal3/selfbuild`. Change the
fragment, not the generated Python: the generated `~/.gal3/*.py` are build
outputs and are overwritten on every build.

## Known CI gaps

- **MUMPS is not on the CI runner.** The compiler emits MUMPS and self-hosts on
  YottaDB, but YottaDB isn't provisioned in CI yet, so the MUMPS oracle cells
  and `./mumpsself` run only locally for now. If your change touches
  `mumps_inference.txt`, run `GAL_ORACLE_LANGS=py,js,mumps gal3/bin/five_oracle.sh`
  and `./mumpsself --quick` locally (both need YottaDB) and say so in the PR.

## License of contributions

By contributing you agree your contribution is licensed under the project's
[Apache-2.0](LICENSE) license. There is no CLA and no relicensing: the engine
stays open, for everyone, permanently.
