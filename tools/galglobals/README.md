# galglobals — the MUMPS global model as a small C library

The persistence and collections runtime planned in
`docs/mumps_design.md` §C′: MUMPS-style global nodes (sparse subscripted
trees with ordered traversal) over ordinary key-value storage, so C and
other targets get ordered maps, dictionaries, open-ended lists and
durable objects from one small API — without MUMPS-the-language.

## Pieces

- `ggencode.h/c` — the crux: an **order-preserving tuple encoding**.
  Subscript tuples serialize to byte strings whose `memcmp` order equals
  MUMPS canonic collation (`""` first, then canonic numbers in numeric
  order, then strings in byte order; non-canonic numerics like `"07"`
  and `"0.5"` are strings). Each subscript encoding is self-terminating
  and prefix-free, so a tuple is a strict byte prefix of its descendants
  — which is exactly what `$order`/`$data` walks need.
- `gg.h` — the node operations: `set`, `get`, `kill` (subtree), `data`
  ($data: 0/1/10/11), `order` ($order, both directions, returns decoded
  subscripts), `increment` ($increment, canonic storage).
- `gg_mem.c` — the in-memory backend (the "locals" tier): a sorted
  array, correctness-first. The same contract is intended to run over
  **LMDB** for the persistent "globals" tier (`gg_open_lmdb`, to come —
  needs `liblmdb-dev`), mirroring MUMPS's `X` / `^X` distinction as two
  backends of one API.

## Tests

`make test` runs both suites: the collation-ordering fixture,
round-trips (including embedded NULs), tuple prefix properties, and
MUMPS-semantics checks of the node ops (valueless parents, mixed
numeric/string `$order` walks, reverse traversal, subtree kill).

YottaDB's SimpleAPI (`libyottadb`) is the semantic reference
implementation — when it is installed, a differential test comparing
`gg_*` behavior against `ydb_*_s` on random trees is the next gate.
