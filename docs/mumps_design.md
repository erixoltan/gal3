# gal3 MUMPS support — inheritance flattening, routine generation, persistent objects

*Study + design proposal, 2026-07-19. Based on a reading of gal2's proven
implementation (`gal2/src/Mumps.gal`, ~3,100 lines; `Inherit` in
`gal2/src/Language.gal`; the runtime `tools/yottadb/routines/gal.m`).
Companion to [java_selfhost_design.md](java_selfhost_design.md) (design
note 1 anticipated this) and [architecture.md](architecture.md).*

## What gal2 built (the study)

### 1. The Inheritance inference — compile-time flattening

`Class_Statement.Inherit` (Language.gal) resolves the class hierarchy at
compile time, recursively and memoized (`Is_Compiled`):

- Each class first `Inherit`s its ancestors (looked up by name through the
  global `Statement_Class:Names` registry, so declaration order never
  matters), then merges their flattened tables into its own:
  `Compiled_Ancestors`, `Compiled_Class_Properties`,
  `Compiled_Class_Methods`, `Compiled_Properties`, `Compiled_Methods`.
- Merge order is ancestors-first, own-members-last into dictionaries —
  **last write wins, so overrides resolve during the merge**. The result is
  a complete member table per class with inheritance already applied.
- A driver (`Compiled_Inheritance`) walks the element list once and calls
  `Inherit` on every class before generation begins. The C generator calls
  the same driver — gal2 already treated this as target-neutral machinery.

The consequence: generators never walk a hierarchy. A "class" at emission
time is a flat bag of members.

### 2. Class → routine emission

Each gal class becomes **one MUMPS routine** named after the class
(underscores stripped). The routine contains:

- a label per member of the *flattened* tables — inherited methods that
  are not overridden are stamped into the descendant's routine verbatim.
  **The flattening is the vtable**: dispatch is a single computed call,
  no runtime MRO walk exists at all.
- `%init(%class)` — idempotent class registration: writes the class's
  metadata global `^%ClassName`, registers it in `^%Classes`, and records
  the full ancestor set under `^%ClassName("Ancestors",...)` (this powers
  runtime `is a` checks against persistent data).
- a synthesized constructor when the class declares none (`new()`
  allocates, blesses, runs property initializations) — the same
  no-ctor-synthesis problem the Java port solved with pass-throughs.
- class properties live in the class's own global: `^%ClassName(0,"Prop")`.

Control flow is label-based: `Get_Label` allocates `L1, L2, …`;
if/else/loops emit labels and gotos (`End_Label`, `Break_Lbl`,
`Continue_Lbl`). A second pass (`Re_Mumps`) regenerates after label
allocation settles.

### 3. The object model and persistence

This is the distinctive part. From `gal.m`:

- `%matrix="^X"` — the object arena **is a database global**.
- `new` = `$name(@%matrix@($increment(@%matrix)))` — an object handle is
  the *name of a global node*. `set @%self=ClassName` blesses it.
- Properties are subscripts of the object's node: `@%self@("Prop")`.
  Lists and dictionaries are sparse subtrees — they need no separate
  representation at all, MUMPS globals *are* sparse dictionaries.
- Because the arena is a global, **every object is durable by
  construction**: restart the process and the object graph is still
  there, with `^%Classes` + per-class `Ancestors` metadata making it
  self-describing. `init^gal` (re)registers all classes in a routine
  directory; `wipe^gal` clears the database.

### 4. The dispatch runtime

`dispatchN^gal(%oid,%method,args…)` (one per arity, mirroring how gal2
handled arity elsewhere): fetch the class name from `@%oid`, then one
computed `do`/`$$` of `method^CLASS(args)`. Single hop, because the
routine already contains every inherited label. Method-call statements
emit `do dispatchN^gal(...)`; call operations emit `$$dispatchN^gal(...)`.

## Why this matters for gal3 — three separable deliverables

### A. The Inheritance inference as a shared gal3 inference

Port `Inherit` into a new `inheritance_inference.txt` in the zero stack
(sibling of attributes/structure/data_type inference): stamp
`Compiled_*` member tables onto `Statement_Class` classifications after
structure inference. gal3 already has the ingredients — the
`Statement_Class:Names` registry exists (attributes_inference fills it),
and the pass is order-independent through it, exactly as in gal2.

Three consumers, in increasing ambition:

1. **MUMPS** (below) — the original customer.
2. **C — this is the key that unfreezes `galc`** (design note 1 of the
   Java doc): flattened member tables mean gal→C needs no vtables and no
   inheritance emulation; a class is a struct layout plus a set of plain
   functions, overrides already resolved. gal2's C generator already
   called `Compiled_Inheritance`.
3. **The typed backends**: the Java port hand-built backend-local
   registries (fields, methods, ancestors, ctor signatures) by walking
   the element list — that is an ad-hoc `Inherit`. A shared inference
   replaces those walks with precomputed tables every backend can trust,
   and is the natural home for the member-type widening the Java backend
   currently does privately. It also dovetails with the typed-member
   plan (design note 3): inferred member types would live on the same
   flattened tables.

Landing pattern: like `data_type_inference` did — behavior-neutral while
no generator consumes it, validated by the 13-artifact fixpoint holding
byte-exact with the pass running in every compile.

**DONE 2026-07-19** — `inheritance_inference.txt` is in the zero stack
(filling the `Infer_Inheritance` stub that had waited in the pipeline),
wired through all thirteen build/verify scripts. Fixpoint 13/13
byte-exact, oracle 26/26, `jsself` green for all twelve rows with the
pass running in every compile. (Those counts are as of that day; adding
`galmumps` later the same week made it 14 artifacts and a 31-cell
oracle.) Functionally verified on a three-level
hierarchy: transitive `Compiled_Ancestors`, full flattened member tables,
last-wins override resolution, class properties propagated,
`Compiled_Constructor` inherited. Two notes: dialect-declared classes
flatten as roots for now (no `Ancestor` property — extend when a consumer
needs their generated ancestry), and the port surfaced a bootstrap catch
unrelated to the inference — the `[return]` literal in a backend source
has no gal2 python generator, so backend sources must use
`(Runtime:Chr 13)` (first full loop since the M3 backend edits caught
it).

### B. A MUMPS backend (`mumps_inference.txt` + `mumps_main.txt`)

Follow the established recipe: a 1:1 mirror of `python_inference.txt`
with MUMPS bodies, wired into `build`/`selfbuild`/`selfself`, plus the
`gal.m` runtime (port of `tools/yottadb/routines/gal.m`, which already
exists and works under YottaDB). Start with the five-programs contract —
a sixth oracle column — then promote using the Java-port playbook.

Expected difficulty profile, informed by the Java port:

- **Easier than Java**: MUMPS is untyped — everything is a string/number
  and globals are duck-typed, so the entire cast/hoist/widening layer the
  Java port needed simply does not arise. Semantically it sits *closer to
  python* than any typed target.
- **The real work**: labels-not-blocks control flow (gal2 solved it:
  label allocator + goto patterns + the `Re_Mumps` second pass — gal3's
  single-pass generation may need the same two-pass wrinkle or a
  deferred-label trick); `new`-scoping of locals; name mangling
  (underscore stripping, historic 8-char pressure); arity-indexed
  dispatch helpers; and the `%init`/metadata emission.
- gal2's 3,100-line generator is the proven reference to port from, the
  same way `Python.gal` seeded `python_inference.txt`.

**STARTED 2026-07-19** — `mumps_inference.txt` + `mumps_main.txt` exist
at hello coverage with the fail-loudly subset contract (java-style
Print_Errors driver, avoiding the C driver's silent-error hole), wired
into `build`/`selfbuild`/`selfself` as the **fourteenth self-hosting
artifact** — fixpoint 14/14 byte-identical — plus stack rows in
`jsself`/`javaself`. hello emits a clean runnable routine (column-one
labels, `do main()` guard before any formallist label, doubled-quote
strings, `use $principal write …,!`); fizzbuzz correctly fails loudly
listing its missing generators (the if/else family, Equal, Modulo).
**CONTRACT COMPLETE 2026-07-19 (same day, YottaDB installed):** all five
programs pass **byte-identical** on MUMPS under YottaDB r2.06 — the
oracle is now 31 cells across six languages. What landed:
- label control flow (if/else chains sharing a position-derived end
  label, for-range and for-each as label loops with `$order` walks) —
  labels derive from element character positions, so no counter state
  and the fixpoint holds trivially;
- one shared-source fix: `structure_inference` now links `Next_Else` on
  the *classifications* (the element-level hook was a no-op — the
  comment 'connect ifs to elses' finally does);
- classes as flattened routines — **the inheritance inference's first
  consumer**: `Statement_Class` reads `Compiled_Properties`/`Methods`/
  `Constructor` straight off the classification; constructors allocate
  `$name(@%matrix@($increment(@%matrix)))`, bless, apply property
  defaults, run the body;
- `bin/galrt.m`, the minimal runtime (matrix init — local `X` by
  default so contract objects are transient; point `%matrix` at `^X`
  for persistence — plus `dispatchN` by arity);
- multi-routine output as a `;;;ROUTINE`-marked bundle the oracle
  splits into per-routine `.m` files;
- lists as numeric-subscript arrays (insertion order = iteration
  order), dictionaries as plain sparse locals, `$get` for dget, `_`
  concatenation for append, write/read for say/readline.
**PROMOTION 2026-07-19 (same day, continued): the gal compiler runs
end-to-end in MUMPS.** All four compiler atomics generate with zero
errors; the compiled compiler zlinks, parses, classifies, and writes
output under YottaDB with `galmatrix=^X` — every object of the run
inspectable afterward via `galdump.m` (census / parser state /
`find^galdump <Class>` / wipe), which is Erik's retrospective-database
workflow and which drove the debugging itself. The port's decisions:
collections are matrix-node **handles** (python reference semantics
exactly — assignment copies the handle), `$select` forms restore
short-circuit and/or, identifiers strip underscores, i-calls go direct
when `Compiled_Methods` proves the label and dispatch otherwise
(necessary because a **latent pipeline bug drops `class set
Compiler`'s `Data_Type_Report`** from every artifact — invisible to
python's dynamism, fatal to static zlink; to be fixed in the splice).
**BYTE PARITY REACHED, and the pipeline is hosted (2026-07-19).** The
MUMPS-hosted compiler compiles all five contract programs *and its own
150KB source* byte-identically to the python host, and `gal`,
`fallback` and `galpy` all run as MUMPS routine bundles, so the whole
`gal -> fallback (to fixpoint) -> galpy` chain executes inside YottaDB
and emits python that is byte-identical and runtime-identical to the
python-hosted chain's.

Eight bugs stood between the first end-to-end run and parity, and each
one is a semantic gap between python and MUMPS worth stating plainly:

1. **Multi-operand declarations concatenate.** `string Code ':' [line]
   Body;` must join *every* value operand (`Mumps_Args '_'`), not just
   the first.
2. **`close` appends a newline when `$X` is nonzero**, and a single
   `write` of a long string hits the device width (32767) - wrapping,
   or truncating under NOWRAP. Write one record per line and zero `$X`.
3. **`NEW` inside a goto-loop leaks.** MUMPS pops a NEW's save entry
   only when the *frame* quits, so a declaration inside a loop pushes
   one entry per iteration and exhausts the stack (~400 statements in).
   Every local now registers via `Mumps_Declare` and is newed once in
   the frame prologue (`Mumps_Hoist`) - which is also exactly python's
   function-scoped locals. Erik's gal2 rule, recovered independently.
   The `$etrap`/`$estack` news moved there too, and a guard restores
   the *enclosing* guard's trap literal (`Mumps_Trap_Value`) instead of
   saving it in a per-site local.
4. **Lists must carry their own count.** `llen` walked the subscripts,
   making `llength` O(n) and the compiler O(n^2): 84KB took 2m29s.
   With a count node maintained by `lpush`/`shift`/`poplast` it takes
   9s. Dictionaries likewise got insertion-order iteration (`dset` with
   `o`/`x`/`k`/`n` nodes) to match python's dict contract.
5. **Python truthiness is not MUMPS truth.** `if [my Value]` on an
   object handle reads numerically as zero - false - where python says
   true. Conditions now go through `Mumps_Cond`, which emits
   `$$truthy^galrt()` unless the operand is definitely numeric.
6. **Unary `'` binds tighter than comparison.** `'A=""` means
   `('A)=""`. Negation must parenthesize its operand first. This one
   silently produced *plausible* output (`pass` instead of a body) for
   as long as it existed.
7. **`is a` on a non-object must answer false, not raise.** `isa`
   indirected the value, so `T is an Element` on the string `'string'`
   raised UNDEF, which the surrounding `forgive` swallowed - quietly
   losing every string-to-numeric conversion. `isa` now checks for the
   matrix-handle shape first.
8. **`None` and `''` are different, and MUMPS can say so.** Python's
   `defined` is `is not None`, and a property declared `''` *is*
   defined. MUMPS has no None - but it does have the difference between
   a node that is absent and a node that exists holding nothing. So:
   **an absent node is None; a node that exists is a value, empty or
   not.** The constructor sets every property that declares a value
   (even `''`) and leaves `[null]`-declared and valueless ones unset;
   `defined`/`undefined` ask `$data`, not `$get`. Note `is null` needs
   no such care - it already means "None or empty" in every backend.
   Without this, a dialect's generated `Initialize` came out with one
   newline missing, and only on the compiler's own source.

   One asymmetry remains, deliberately: a property *declared* `[null]`
   is absent (undefined), but a property *assigned* `[null]` at runtime
   is set to `""` and so reads as defined, where python would report
   None. Making assignment `kill` the node would close it. Every
   generator that has to distinguish the two currently tests
   truthiness (`if [my Value]`), which is correct either way, and the
   whole compiler source lowers byte-identically as it stands - so this
   is recorded rather than fixed, to be revisited if a divergence ever
   traces back to it.

**The gate: `./mumpsself`, green at 22 checks (2026-07-20).** It emits a
routine bundle per artifact (phase A, javac's role played by YottaDB's
zlink on first use), then runs the whole pipeline hosted in MUMPS against
the Python-hosted chain (phase B) and demands byte-identical output at
every stage. Rows: the five contract programs — each of `gal`, `fallback`,
`galpy`, plus a check that the emitted Python *runs* identically — and
the compiler's own 150KB source through all three stages, including the
full `fallback` fixpoint. `--quick` drops the compiler-source row for a
two-minute answer; the full run takes about an hour, the fallback fixpoint
being the long pole (a single pass over 165KB is ~14 minutes).

Companion tools: `bin/mchain.sh` compiles one program through the hosted
chain; `tools/yottadb/routines/galdump.m` inspects the objects a run left
behind (`galmatrix=^X`); `galprof.m` profiles a run line by line via
`VIEW TRACE`. Performance is minutes, not seconds — roughly 100× the
Python host — and the profile is flat (dispatch, list/dict primitives,
`isa`), so there is no single hot spot left to remove, just scale.

### C′. The KV-store globals runtime — Erik's unrealized plan for C

(Recorded 2026-07-19.) The plan: map the **MUMPS global structure onto an
ordered key-value store** — LMDB or Berkeley DB — as the persistence and
collections backend for C and other languages. The global model was
already the solved design (ordered maps, dictionaries, open-ended lists
all fall out of sparse subscripted nodes with ordered traversal); the KV
store supplies exactly that machinery without MUMPS-the-language's
limitations.

Why this is the right shape:

- A global node is `(name, subscript-tuple) → value`; `$order`/`$query`/
  `$data` are ordered-cursor operations. An LMDB/BDB B-tree is precisely
  an ordered `key → value` map with cursors — the semantic match is
  one-to-one.
- **The technical crux is the key encoding**: subscript tuples must
  serialize to byte strings whose bytewise order equals MUMPS canonic
  collation (numeric subscripts numerically first, then strings
  lexically). This is a known, solved problem — FoundationDB's tuple
  layer, the SQLite4 key encoding, and YottaDB's own internal subscript
  encoding are all prior art for order-preserving tuple encodings (type
  tag + order-preserving number normalization + escaped strings).
- With that encoding, the whole gal2 object model transfers verbatim: an
  object handle is an encoded key prefix (the `$name` analogue), bless =
  write the class at the prefix root, properties/lists/dictionaries are
  subtrees, `$order` walks are `MDB_SET_RANGE` cursor seeks, `$data` is a
  prefix probe, `$increment` an atomic counter.
- **This is the other half of unfreezing `galc`.** The C target froze on
  "hand-build a string/collection/object runtime." Flattened inheritance
  (§A) removes the object-model problem; the globals-on-KV runtime
  removes the collections problem — objects, dicts, lists, and class
  metadata all become *one* small C API (roughly: `set/get/kill/data/
  order/increment` + tuple encode/decode) over the store. Strings remain
  the one genuinely hand-rolled piece.
- **Locals vs globals maps to two backends of the same API**: MUMPS
  distinguishes process-local arrays (`X`) from database globals (`^X`).
  The C runtime mirrors that — transient collections over an in-memory
  ordered map (or an LMDB env on tmpfs), persistent ones over the durable
  LMDB file. Same operations, one flag.

Backend choice notes:

- **LMDB** is the strong default: permissive OpenLDAP license, tiny,
  single-file mmap, zero-copy reads, crash-safe, C-native, ubiquitous.
- **Berkeley DB** carries the AGPL problem since 6.x (older BSD-licensed
  5.x exists but is frozen) — probably only worth it where its page
  layout or existing deployments matter.
- **YottaDB's SimpleAPI deserves a look as a third option/reference**:
  `libyottadb` exposes globals *as a C API* (`ydb_set_s`,
  `ydb_node_next_s`, …) — literally "globals without MUMPS", collation
  included. Heavier and Linux-centric, but it is the semantic reference
  implementation, and a pluggable runtime (same gal API over LMDB for
  portability, over YottaDB when the real database and MUMPS interop are
  wanted) keeps both doors open.

**Key-layout note (Erik's original design, discussed 2026-07-19).** The
plan Erik had sketched for C: sort data at the front — each subscript
opening with a type tag so numbers collate before strings — and the
structural metadata at the back (one length byte per subscript, final
byte the subscript count; both capped at 255, comfortably above MUMPS's
own 31-subscript / key-size limits). The insight — collation bytes
first, structure last — is exactly right and is what the implemented
codec achieves; the difference is how subscript *boundaries* stay out
of the comparison. With raw concatenated sort bytes, a subscript
containing a byte lower than the type tags can collide across
boundaries: ("A\x01") encodes sort-bytes T,'A',0x01 which memcmp-sorts
*before* ("A","A")'s T,'A',T,'A' — yet the whole ("A") subtree must
precede ("A\x01"). That is safe when subscript content is guaranteed
above the tag range (typical MUMPS text), but not for arbitrary bytes.
The implemented codec instead makes each subscript self-terminating
(0x00 terminator, interior 0x00 escaped as 0x00 0xFF), which yields the
same front-loaded collation plus two extras: boundary-safety for any
byte content, and the parent key being a literal byte-prefix of every
descendant key — which is what makes $order/$data/kill plain cursor
range operations. If the trailing-metadata layout is ever wanted (raw
unescaped content, simpler decode), it can live as a second codec
behind the same gg API — the node operations don't care which encoding
produced the keys.

One language-level dividend beyond persistence: a **canonically ordered
map element**. gal's dictionaries currently inherit python's
insertion-order semantics, which the Java port had to reproduce with
LinkedHashMap, and which no two targets share natively. A `sorted
dictionary`/ordered-map element defined by MUMPS collation would have
*identical iteration order on every target by definition* — the KV
runtime gives it to C for free, and the scripting targets implement it
with a sort or a tree. That removes a whole class of cross-target
ordering divergences at the root.

### C. Persistence as a language surface

gal2's objects are persistent *by default* on MUMPS — that falls out of
the representation. For gal3 this is prime territory for design note 2
(higher-level elements, per-target implementations):

- Near term: keep it a property of the MUMPS target — compiling gal to
  MUMPS gives you durable objects and a self-describing object database
  for free, which is already a distinctive story (no other mainstream
  compiler target makes *every object* a database row).
- Later: a declared surface — e.g. a `persistent` class modifier or a
  `database` element — that MUMPS implements natively and other targets
  implement with their own machinery (sqlite, files) or reject loudly.
  The dialect gives the same outcomes where implemented; targets without
  an implementation simply don't claim the feature.
- A further thought worth keeping: a persistent element store means the
  *compiler's own element trees* could live in the database — the seed of
  incremental compilation on the MUMPS target.

## Suggested sequencing

1. **Inheritance inference** (shared, small, fixpoint-validated,
   immediately useful to Java and prerequisite to both C and MUMPS).
2. **MUMPS subset backend** — five-programs contract, sixth oracle
   column, `gal.m` runtime revived under YottaDB (tooling already in
   `tools/yottadb/`).
3. **The globals-on-KV C runtime (§C′)** — the tuple encoding plus the
   half-dozen node operations over LMDB, testable standalone against
   YottaDB behavior long before the C backend consumes it. Together with
   §A this is the credible path to unfreezing `galc`.
4. **Promotion + persistence surface** — full coverage via the Java
   playbook (probe → javac-equivalent gate is the YottaDB compile →
   behavioral stage diffs), then decide how much of the persistence
   model to lift into the dialect (`persistent`, and the ordered-map
   element from §C′).
