# gal3 JavaScript toolchain — running the compiler in JS

*Design document, 2026-07-16 (rev 4 — post-review corrections: the
missing-key dict decision reversed after checking the Python backend's
actual emission; milestone-2 constructor rules completed; risk register
re-verified against the sources. Only the version stamp remains open).
Companion to [architecture.md](architecture.md) and
[status.md](status.md).*

## Goal

Take the `_33` fixpoint compilers and use them to produce a **JavaScript
edition of the gal3 compiler itself**: `gal.js`, `fallback.js`, `galpy.js`,
`galjs.js` (and later `pygal.js`), runnable under node. The correctness bar
is the same one gal1 met when its Python and JavaScript compilers compiled
gal1 to byte-identical code:

> Every artifact the JS compilers produce is **byte-identical** to what the
> `_33` Python compilers produce from the same input — at every pipeline
> stage (`.gal`, `.atomic`, `.py`, `.js`).

Because equality holds stage by stage, **interoperability falls out for
free**: any mixed chain (e.g. `node gal.js` → `python fallback_33.py` →
`node galpy.js`) produces the same bytes as either pure chain. The stage
diffs *are* the interop guarantee.

We are **not** asking gal2 to produce a working JS compiler. `galjs.py` and
`galjs_3.py` are allowed to emit broken JS; bootstrap stays Python-only
(gal2 → `_3` → `_33`), and JS grafts onto the chain only at the `_33`
generation.

## Why this is cheap

1. **The atomics already exist.** `selfself` leaves `${a}_33.atomic` (and
   `.tx2`, `.gal`, `.py`) in `~/code/gal3build/`. Emitting the `.js` files
   is one run of `galjs_33.py` per artifact — seconds, not a fixpoint loop.
2. **JS-backend fixes never need the full loop.** `javascript_inference.txt`
   and `javascript_main.txt` appear only in the **galjs** source stack — not
   in gal, fallback, or galpy. After a JS-only edit, rebuilding
   `galjs_33.py` alone with the existing fixpoint binaries
   (`gal_33.py → fallback_33.py* → galpy_33.py`) produces exactly what the
   full `build && selfbuild && selfself` would produce, because every
   compiler in that chain is unchanged and `_3 ≡ _33`. One artifact, one
   pass.
3. The expensive full loop is needed only when **shared** sources change
   (`gal_base`, `fallback_inference`, `compiler_dialect`, the `_main` files,
   the zero stack) — those changes are batched into their own milestones
   below.

## Milestones and sequencing

The shared-source changes are deliberately separated from the JS-backend
work so that JS iteration always runs against a *stable* `_33` ground truth.

- **Milestone 0 — one full loop (shared prep).** Turn off `.elems` emission
  (see below). Re-stamp the fixpoint. Small, low-risk, verifies the loop
  discipline before the real work. **DONE 2026-07-16** (13/13 fixpoint
  diffs clean, oracle 26/26).
- **Milestone 1 — JS chain green.** All work is JS-backend-only
  (`javascript_inference.txt` / `javascript_main.txt`), iterated on the
  cheap `galjsbuild` path: Map dictionaries, `debug;` → error, inline
  Runtime include, plus whatever the stage diffs surface. Done when
  `jsself` is green for `gal fallback galpy galjs`. **DONE 2026-07-16**
  (same day) — see "What milestone 1 actually surfaced" below.
- **Milestone 2 — Base/constructor/super redesign (full loop).** The
  language-level change removing the implicit-Base requirement, applied
  across fallback + all five backends, with the new explicit `super`
  statement. Re-run the full loop **and** `jsself` — the JS chain now
  serves as a second, independent verifier for this change.
- **Milestone 3 — pygal.js and the rest.** pygal (deferred: 1.8 MB atomic,
  memoization/left-recursion machinery never yet through galjs), then
  `pylex`/`pyparse`/`pygen` as more rows in the same loop. Browser-JS
  inference (see below) whenever it's wanted. **DONE 2026-07-16** (browser
  inference excepted — still open) — see "What milestone 3 actually
  surfaced" below.

## Scope (milestone 1)

**In:** `gal`, `fallback`, `galpy`, `galjs` — the minimal self-hosting set:
front end + lowering + both self-hosting backends.

**Deferred, and why:**
- `pygal` — deferred by decision (2026-07-16); it should eventually work in
  JS and every other target, but it is the long pole and proves no new
  mechanism the four don't.
- `peg` — not needed even for pygal: `python_parser.txt` is baked into
  `pygal_33.tx2`; the JS chain consumes the `.tx2`, never regenerates the
  parser.
- `pylex`, `pyparse`, `pygen`, `galgo`, `galjava`, `galcpp` — more rows
  later.

## The build scripts

Two new scripts in `gal3/`, following existing naming conventions.

### `jsself` — emit and verify (the main event)

Precondition: a completed `build && selfbuild && selfself` (the `_33`
artifacts in `$BUILD` are ground truth). Two phases.

**Phase A — emit** (seconds):

```bash
for a in gal fallback galpy galjs; do
    python ~/.gal3/galjs_33.py "$BUILD/${a}_33.atomic" "$BUILD/${a}.js"
    node --check "$BUILD/${a}.js"     # syntax gate before anything runs
done
```

Phase B runs the compilers out of `$BUILD`; the `cp` into `~/.gal3/`
happens only **after all stage diffs are green**, so the install dir never
holds an unverified JS compiler (a broken `gal.js` in `~/.gal3` is a
future mystery for someone).

**Phase B — the JS chain rebuilds the compiler, diffing every stage:**

```bash
for a in gal fallback galpy galjs; do
    # staleness guard: re-concatenate the source stack (same cat list the
    # build scripts use) into ${a}_j.tx2 and require it to match the .tx2
    # the _33 loop consumed; abort with "run the full loop first" if
    # sources drifted since the last selfself.
    cat <the ${a} stack>       >  "$BUILD/${a}_j.tx2"
    cmp "$BUILD/${a}_j.tx2" "$BUILD/${a}_33.tx2" || abort

    node "$BUILD/gal.js"      "$BUILD/${a}_33.tx2"  "$BUILD/${a}_j.gal"
    diff "$BUILD/${a}_j.gal"    "$BUILD/${a}_33.gal"    || abort

    # fallback to fixpoint — SAME termination rule as build/selfbuild
    # (iterate until output ≡ input), so ${a}_j.fb0.. line up pass-for-
    # pass with the Python chain's fbN files for divergence hunting
    node "$BUILD/fallback.js" ... →  "$BUILD/${a}_j.atomic"
    diff "$BUILD/${a}_j.atomic" "$BUILD/${a}_33.atomic" || abort

    node "$BUILD/galpy.js"    "$BUILD/${a}_j.atomic" "$BUILD/${a}_j.py"
    diff "$BUILD/${a}_j.py"     "$BUILD/${a}_33.py"     || abort

    node "$BUILD/galjs.js"    "$BUILD/${a}_j.atomic" "$BUILD/${a}_j.js"
    diff "$BUILD/${a}_j.js"     "$BUILD/${a}.js"        || abort   # JS fixpoint
done
cp "$BUILD"/{gal,fallback,galpy,galjs}.js ~/.gal3/   # install only on green
```

Notes:
- `_j` suffix = "produced by the JS chain". Mirrors `_3`/`_33` generational
  naming without colliding with it.
- The last diff is the **JS fixpoint**: JS-built-JS ≡ Python-built-JS.
- Stop at first mismatch by default (localizes the bug to one artifact ×
  one stage × one input file); `--keep-going` to survey total damage.
- Accepts artifact names as arguments (`./jsself gal fallback`) so early
  iteration doesn't pay for the whole set.

### `galjsbuild` — fast JS-backend iteration

For edits confined to `javascript_inference.txt` / `javascript_main.txt`:
re-concatenate the galjs stack (zero + gal_base + fallback_inference +
javascript_inference + llm_inference + javascript_main), then compile it
with the fixpoint binaries — `gal_33.py`, `fallback_33.py` (iterated),
`galpy_33.py` — writing `galjs_33.{tx2,gal,atomic,py}` in `$BUILD` and
installing the new `galjs_33.py` in `~/.gal3/`. This keeps `jsself`'s
staleness guard coherent.

`galjs.py` and `galjs_3.py` go stale during this loop — acceptable, they're
bootstrap-only. The full loop re-establishes them at milestone boundaries.

**Discipline:** the moment a fix touches a *shared* source file,
`galjsbuild` is no longer valid — run the full loop.

### The workflow, end to end

```
edit javascript_*.txt  →  ./galjsbuild  →  ./jsself [subset]  →  first diff
        ↑                                                            |
        └──────────────── localize & fix ←───────────────────────────┘
…until jsself is green; then one full
./build && ./selfbuild && ./selfself && ./jsself  to stamp the milestone.
```

## Design decisions (settled 2026-07-16)

### Includes: elements inform the module; inline helpers; Runtime.js last

The gal2 pattern of leaning on an external `Runtime.js` is retired. gal3
uses three tiers, in order of preference:

1. **Standard-package requires, informed per element.** An element that
   needs a package tells its module (`Module.Add_Include`), and the module
   emits the `require` once, deduped — exactly how `fs` works today
   (`Statement_File_Read`, `Statement_Write_To`, `Statement_Readline`).
2. **Inline emitted helpers.** Operations/statements needing executable
   statements emit a helper function or class into the module via
   `Add_Include` — the existing `Gal_Readline` pattern. This includes
   `Runtime:` calls: when the receiver is `Runtime` (same receiver-check
   hook as `Python_Runtime_Include`, python_inference.txt:260), the JS
   backend adds an inline `class Runtime { static Chr(N) { return
   String.fromCharCode(N); } }` include. The four milestone-1 artifacts use
   **only `Runtime.Chr`** (verified by grep over the `_33.py` files —
   `gal` and `fallback` use no Runtime calls at all; only galpy/galjs use
   `Chr`), so **milestone 1 ships with no Runtime.js file at all.**
3. **External `Runtime.js`** remains the escape hatch for heavyweight,
   node-only operations (`Shell_Capture`, `Apply_ED_Script`,
   `Compile_With_LLM`) if an artifact ever needs them.

Tier 2 is also what makes the **browser target** possible: browsers have no
`require()`, so anything inlined survives unmodified.

### Dictionaries: `Map`

Decided: dictionaries compile to `Map`, not plain objects. `Map` is the
only JS structure with Python-dict fidelity on all three axes:
- **insertion order** for *all* keys (objects reorder integer-like keys);
- **no prototype pollution** (`'constructor' in {}` is true; `Map.has`
  has no such trap — and `constructor` is a real gal keyword the compiler
  keys dictionaries with);
- **key identity**: `Map` keeps integer `5` distinct from string `"5"`,
  exactly like Python; objects collapse them.

Surgery checklist (all in `javascript_inference.txt`, all fast-path):
- `Statement_Dictionaries` → `var D = new Map();`
- `Statement_Dictionary` (the singular `dict D;` declaration — a separate
  generator, easy to miss) → `new Map()` likewise
- class-field / static dictionary defaults → `= new Map()`
- `Operation_Dict_Get` → `D.get(K)` — see below
- dict set (`d=`) → `.set(K, V)`
- `Operation_Dict_Exists` → `.has(K)`
- `Statement_Iterate` → `for ([K, V] of D)` (Map iterates entries natively)
- dict length → `.size`
- any dict literal → `new Map([[k, v], …])`
- `Shell_Capture` returns a dictionary — tier-3/deferred, but when it
  lands its JS body must build a Map, not an object, or `dict exists` /
  iterate on its result silently misbehave.

**Missing-key fidelity (decided — REVERSED from rev 3):** rev 3 assumed
Python dict reads raise `KeyError` and prescribed a throwing
`Gal_Dict_Get` helper. That premise is **wrong**: the Python backend emits
`Dictionary.get(Key)` (python_inference.txt:1141), which returns **`None`**
on a missing key — and the compiler sources are written against that
contract (`gal_33.py:168` assigns `Qend.get(C)` unguarded; `gal_33.py:275`
gets-then-dereferences inside a forgive, relying on `None.attr` →
`AttributeError`). A throwing helper would therefore *diverge from ground
truth*, crashing the JS chain where the Python chain proceeds with `None`.

Decided: dict reads emit bare **`D.get(K)`**. `undefined` then plays the
role of `None` correctly, because the JS backend's null checks are all
loose (`Operation_Defined` → `!= null`; `Operation_Is_Null` →
`== null || === ''`), the append/format generators already guard with
`if (arg == null) throw` (javascript_inference.txt:1180, 1214) — mirroring
Python's TypeError on `str`+`None` — and `undefined.attr` throws just like
`None.attr`, so forgive-guarded flows agree. The residual divergence is
**arithmetic on a missing-key result**: Python throws `TypeError`
(`None + 1`), JS silently yields `NaN` (`undefined + 1`) — see the risk
register. No helper; no `Gal_Dict_Get`.

### `debug;` → runtime exception (node); `debugger;` (browser)

Decided: in the **node** inference, `debug;` lowers to the equivalent of
`error "Debugger not implemented";` — i.e.
`throw new Error("Debugger not implemented");`. Rationale: the `debug;`
statements in the compiler mark error conditions that no longer occur in
practice but could in edge cases; an exception is the loud, unattended-safe
substitute for dropping into a debugger. It is *not* a compile-time error —
it only matters if execution reaches it. The future **browser** inference
lowers `debug;` to `debugger;`, which works there.

### `.elems` emission: error-path diagnostic only (milestone 0)

The `.elems` reports existed to (a) produce training data and (b) feed the
LLM-inference workflow (give an LLM the element list, ask it to fill in
target code for unclassified elements). Neither is active.

Mechanism (decided 2026-07-16, superseding the rev-3 flag idea): `.elems`
is written **only on the error path** — the pattern the go/java/cpp/c and
fallback mains already used. The unconditional/success-path writes in
`gal_main`, `python_main`, `javascript_main`, and `peg_main` move into (or
are dropped in favor of) their error branches, where the element report is
a genuinely useful failure diagnostic. No flag machinery; a green build
emits no `.elems` at all. `pyparse` and `nsl` are untouched — their
element report *is* the primary output, not a side file. When
training-data production resumes, reintroduce a switch then. This touches
shared `_main.txt` files, hence full loop, hence milestone 0. `jsself`
correspondingly diffs only the primary outputs — no `.elems` diffs.

### No implicit Base; real constructors and `super` (milestone 2)

Decided in principle: gal3-generated code must **not** require a `Base`
class — that was a gal2-era requirement. Constructor and super logic should
just work in every target. Design sketch:

- **Drop the fallback lowering that appends ` is Base`** to ancestor-less
  classes (fallback `Statement_Class` generator). Programs may still
  declare and use their own `Base` (the compiler sources do — that's
  ordinary code and keeps working).
- **Ancestor-less classes** emit no `extends`/base-class clause and no
  super call in their constructors: JS `class X { }`, Python `class X:`,
  Java no `extends`, C++ no base list, Go struct without embedding.
- **New explicit `super` statement** in the dialect, e.g. `super A B;`,
  with a fallback lowering so every backend sees a uniform element.
  Generalization requirement: the super arguments must be available as
  *data on the constructor element* (e.g. lowered into a `Super_Args`
  property), not merely as a body statement — because C++ must emit it in
  the constructor's **initializer list** and Go must emit it as embedded-
  struct initialization, both *outside* the body. JS/Python/Java can then
  render it in-body (`super(A, B);` / `super().__init__(A, B)` /
  `super(A, B);`) from the same data.
- **Derived-class default** (decided): a derived class that writes no
  explicit `super` passes **nothing** to the parent constructor —
  `super()` / `super().__init__()` / language equivalent. The alternative
  (`super(...arguments)`, today's implicit behavior — see
  javascript_inference.txt:863) would just recreate the arg-sink pattern
  in new clothes. Passing nothing is what makes constructors "just work"
  honestly; the migration audit below adds explicit `super` statements
  wherever parent init actually needs args.
- **No-constructor derived classes** (REVISED at implementation): no
  synthesis. A derived class without properties and without a constructor
  inherits the parent constructor natively — Python and JS do this
  *identically* (full forwarding), and Go/Java/C++ don't implement
  inheritance at all (see below), so there is no cross-target disagreement
  to enforce away. A derived class with properties but no constructor gets
  Python's existing synthesized `__init__` (which already passes nothing
  and conditions its `super()` on having an ancestor); JS covers the same
  case with class fields, which need no constructor. Pass-nothing is a
  rule about *written* constructors only.
- **Go/Java/C++ discovered out of scope**: those backends implement no
  inheritance whatsoever ("the universal Base of a standalone program
  vanishes" — their own comments). `super` is therefore a Python+JS
  feature; a program using `super` against a static backend hits the
  standard unimplemented-element error, which is the correct loud
  behavior. The Super_Args-as-constructor-data generalization is deferred
  to whenever those backends gain inheritance.
- **Super call position: first, enforced in two layers.** The fallback
  lowering errors when `super` appears outside a constructor or in a class
  with no ancestor; the Python and JS constructor generators error when a
  `super` is not the first statement of the block. The explicit super then
  renders in place as the first body statement. Known asymmetry: JS class
  fields initialize *after* `super()` runs, while Python's property
  defaults render *before* the in-body super call — observable only when a
  parent constructor writes a property the child also declares with a
  default. Accepted for now; the fix (render block-minus-super with
  propinit after the super line) is mechanical if it ever matters.
- **Migration audit**: today Base's universal arg-sink constructor absorbs
  whatever child constructors pass up. Some existing chains in
  `compiler_base.txt` appear to pass arguments toward parameterless parent
  constructors (e.g. the `Flag`/`Integer`/`String` symbol classes passing
  `(Object, Value)` up to `Symbol`) — tolerated today only because of the
  sink. Making super explicit will surface every such case; each needs an
  explicit `super` or a signature fix. This audit is the real work of
  milestone 2 and is why it runs *after* the JS chain is green: the JS
  chain then acts as a second independent verifier of the redesign.

### Browser JS: implemented (2026-07-16)

The seam paid off. Shipped as three pieces, none touching shared sources
(so no full loop):

- **`Javascript_Browser_Compiler is Javascript_Compiler`** in
  javascript_inference.txt, whose constructor raises a `Browser_Mode`
  *class* property; the `Javascript_Browser` probe reads it. (A per-
  document mark was the first attempt, but elements only link back to the
  **parser**, which knows nothing of the compiler driving it — so the
  mode is process-global, and hosts that alternate modes reset it between
  stages, as web_main does.) The six node-ism generators branch on the
  probe: file read/write/exists → a **`Gal_Files` Map on `globalThis`**
  (the virtual file system pages preload and read back), `main` → a
  callable **`globalThis.Gal_Main(args)`** instead of `process.argv`,
  `readline` → throw, `debug;` → `debugger;`.
- **`galjsb`** — the browser-emitting backend (galjs stack +
  `javascript_browser_main.txt`), built by `./webbuild` with the fixpoint
  binaries.
- **`galweb.js`** — the whole pipeline as ONE bundle (~491 KB): front end
  + fallback + python + javascript backends + a `web_main.txt` dispatcher
  (`Gal_Main(Stage, Source, Target)`, stages `gal`/`fallback`/`python`/
  `javascript`/`browser`). One bundle because separate per-artifact
  scripts would collide on class names in a shared page global scope.
  `webbuild`'s hygiene gate loads the bundle in a `vm` context with **no
  `require` and no `process`** (a grep would false-positive on the
  generator sources the bundle itself contains).

Verified: the bundle, in a node `vm` browser-context, compiles `bank`
through every stage **byte-identical to the Python chain**, and its
`browser`-stage output runs in another bare context with output identical
to the node edition. Live demo: the *gal playground* artifact (editor →
stage tabs → run-in-page). Known wart: every browser-mode `main` exports
the same `globalThis.Gal_Main` name, so a page that compiles *and* runs
programs must save/restore the compiler's binding around program
execution (the playground does).

### The original seam notes (for reference)

Goal (deferred, but shaping decisions now): compile to browser JS as well
as node, via a **slightly different inference** for the browser. The seam:
- Node-specific generation is already isolated in a handful of generators:
  file I/O (`fs`), `process.argv` (`Statement_Main`), `process.stdout`,
  `process.exit`, `Statement_Readline`. A browser inference swaps these
  bodies (or omits them — browser artifacts are library-style, no CLI
  main); everything else is shared.
- Tier-2 inline helpers keep the shared core dependency-free.
- `debug;` maps per-inference: exception (node) vs `debugger;` (browser).
- Structure to mirror: the backend-pair convention. Whether browser JS is a
  full sibling pair (`javascript_browser_inference.txt`) or a thin overlay
  on the node backend is a milestone-3+ decision; nothing in milestone 1
  should hard-wire node-isms outside the generators listed above.

## What milestone 1 actually surfaced (2026-07-16)

Beyond the planned Map/debug/Runtime surgery, five bug families — recorded
here because every one generalizes past the compiler sources:

1. **Methods go in `class set Spell`, not the `generator` block.** A
   `method` declared among `generate` entries compiles to a module-level
   Python function; `i Method_Name` then dies (silently, under forgive).
   `Python_Runtime_Include` lives in Spell for this reason; so does
   `Javascript_Runtime_Include` now.
2. **The strict-mode `var` family.** JS class bodies are always strict
   mode, so any gal statement that *declares by assignment* (Python needs
   nothing) must emit `var`: `list … copy`, `split`, `join`, and the
   for-range init. Dotted targets (property assignment through the same
   statements) must NOT get `var` — the generators test for `.` in the
   rendered target.
3. **Descending for-range never ran.** The old condition was `<=`
   unconditionally; Python's `range(S, E+1, -1)` needs `> E+1`. A literal
   step decides the direction at compile time; a variable step emits a
   runtime ternary (bounds re-evaluate per pass, unlike `range` — fine for
   the simple names the sources use). Policy (Erik): the programmer should
   declare the loop variable; the emitted `var` covers legacy undeclared
   loops either way.
4. **The compiler shadows JS built-ins.** The sources declare `Symbol`,
   `Number`, `String` (etc.) classes; a module-level class binding shadows
   the built-in across the *entire* module scope (TDZ included, so a
   top-of-file alias can't fix it). All emitted built-in references go
   through `globalThis.String(…)` / `globalThis.Number(…)`.
5. **`Gal_New` proxy for AttributeError parity (decided).** Python's
   missing-attribute read throws; JS yields `undefined` — and
   forgive-guarded reads like `Gal_Block`'s `Code = [my Block Gal]` depend
   on the throw (risk register #2, exactly as predicted). A read-side
   helper was rejected because `Syntax_My`/`Syntax_Property` chains also
   appear in *write* position (assign, append, increment), which a
   helper-call rendering would break. Instead `Operation_New` emits
   `Gal_New(Class, args)`, a tier-2 inline helper that wraps every gal
   object in a `Proxy` whose `get` throws on missing properties (symbol
   keys and `in`-visible properties pass through). Writes and method calls
   are untouched; identity is stable (wrapped once at construction); and
   the mechanism is per-instantiation, so it survives milestone 2's Base
   removal. Known cost: proxied reads are slower — acceptable until
   profiling says otherwise. Known gap: reads inside a constructor body see
   the raw object (Python parity is close enough: `__init__` reads of
   unset attributes throw there too).

## What milestone 2 actually surfaced (2026-07-16)

1. **gal2 and gal3 disagree on `defined` semantics** — the milestone's
   biggest lesson. gal2 compiles `defined [X.P] { body }` as an
   attribute-*exists* probe with the body *inside* the try; gal3's
   backends compile an explicit `is None` check. Under gal2-built `_0`
   binaries, dialect-declared optional properties exist as `None`, so an
   exists-check is always true — the old generators only behaved because
   their bodies dereferenced the `None` and crashed inside the absorbed
   try. A `defined`-guarded body that *doesn't* crash (like setting a
   flag) silently behaves differently per generation. The regime-proof
   idiom, used by all three new ancestor checks:
   `forgive { string Probe ([Cls.Ancestor].Get_Input); Has_Ancestor = 'y'; }`
   — the dereference throws on unset (missing attribute *or* null) under
   gal2- and gal3-built binaries alike, and under the JS chain's Gal_New
   proxy.
2. **`error` inside `forgive` is self-swallowing.** The misplaced-super
   validation originally raised inside its own scan forgive and vanished.
   Scan sets a flag; the error fires outside.
3. **The migration audit came to exactly two source fixes**, both
   parameter defaults: `Generator`'s `constructor [object O [null]]`
   (compiler_base) and the generated `X_Generator` template's
   `constructor [object Owner [null]]` (fallback_inference) — the second
   found only when `selfself` crashed on the `Fallback_Generator is
   Gal_Generator` chain, which the static audit missed because generator
   classes chain to *each other*, not just to `Generator`. The symbol
   classes (`Flag`/`Integer`/`String`… passing `(Object, Value)` toward
   `Symbol`) turned out to be dead chains — never instantiated, latent
   TypeErrors even before M2.
4. **Programs no longer need `class Base;` at all.** The test program
   (`super_test`) declares none, uses explicit `super Name 'woof';`,
   fewer-args super, a pass-nothing chain, and a no-ctor derived class —
   byte-identical behavior in Python and node. The five example programs'
   `class Base;` declarations are now vestigial but harmless.

## What milestone 3 actually surfaced (2026-07-16)

The punchline: **nothing**. All eight new rows — `pylex`, `pyparse`,
`pygen`, `galgo`, `galjava`, `galcpp`, `galc`, and `pygal` itself — went
through the JS chain green with **zero new backend fixes**. The
milestone-1 bug families (strict-mode `var`, Map surgery, `Gal_New` proxy,
`globalThis` shadowing) were general enough to cover the peg-generated
parser's memoization/left-recursion machinery and every language backend.
`jsself` now verifies 12 rows × 4 stages; on full-set green it installs
all twelve `.js` artifacts.

Behavioral corroboration beyond the stage diffs:
- `pylex.js` / `pyparse.js` / `pygen.js` produce byte-identical output to
  their `_33.py` editions on real Python input (zdebug.py: 187 KB token
  stream, 1.6 MB element tree, 65 KB normalized source).
- `pygal.js` translates 4 of the 5 five-languages program artifacts
  byte-identically. The fifth (checkout) fails **identically in both
  editions** ("pygal: call to unknown function input" — a pre-existing
  pygal limitation), and `pylex_33.py` is untranslatable in both editions
  (pre-existing `Pyc_Return`/`Gal3_Stmts` gap). Failure parity is itself
  evidence the chains agree.
- Perf note: the node chain runs ~2× slower than CPython on the big
  translation workloads (the `Gal_New` proxy tax; e.g. pygal on
  pylex_33.py: ~36 s Python vs ~70 s node). Acceptable; revisit only if it
  starts to matter.

Still open from the original milestone-3 list: the **browser inference**
(a node-free `javascript_browser` variant) — deferred until wanted.

## Definition of done (milestone 1)

- `./jsself` green: 4 stage-diffs × 4 artifacts, all empty.
- The structural fixpoint is corroborated behaviorally — and here the two
  chains are *different implementations*, so agreement is far stronger
  evidence than Python-vs-Python was. Still, run the oracles:
  `bin/five_oracle.sh` unchanged, plus at least one cell where the
  *compiler* runs under node (e.g. `node ~/.gal3/galjs.js t.fb1 t.js`).

## Remaining gaps and risk register

Byte-identity killers found by inspection (2026-07-16), beyond the settled
decisions above:

1. **Silent `NaN` — the sharpest silent-divergence family.** Two sources:
   (a) *arithmetic on a missing-key dict read* — Python `None + 1` throws
   `TypeError` loudly, JS `undefined + 1` yields `NaN` silently. Concrete
   shape already in the sources: `gal_33.py:983` computes
   `Candidates.get(Bef) + 1` (safe today — an `in` check precedes it — but
   it is exactly the pattern). (b) *string→numeric conversion*: the
   data-type-driven conversion emits `Number(x)`
   (javascript_inference.txt:334, 368); Python `int('abc')` throws,
   `Number('abc')` is `NaN` and propagates until it stringifies as `'NaN'`
   far downstream. **Debugging rule: on any mysterious stage diff, grep
   the diverged output for `NaN` first.**
2. **Exception-shape differences under `forgive`.** JS throws in fewer
   places than Python. Partially pre-mitigated: `Operation_Defined` uses
   loose `!= null` (catches `undefined`), the append/format generators
   throw on `== null` args (mirroring Python's TypeError on `str`+`None`),
   and `undefined.attr` throws like `None.attr`. What remains: compiler
   control flow relying on a Python-side throw that JS doesn't reproduce
   (e.g. the `NaN` family above inside a forgive) — a likely family for
   the first mysterious stage diff.
3. **Number formatting.** `str(4/2)` = `'2.0'` in Python vs `'2'` in JS.
   *Verified 2026-07-16: the four `_33.py` artifacts contain no `/` and no
   `%` at all* — currently vacuous, kept as a guard: any new division in
   the stacks reopens it. Negative modulo also differs (`-1 % 3`: 2 vs -1)
   — no known use.
4. **Code points vs UTF-16 units.** Identical for the BMP; the sources'
   non-ASCII (curly quotes and `«»`/`‹›` guillemots, all in the quote
   machinery and comments) is verified all-BMP. One astral character would
   silently shift `substring` offsets. `jsself` grep-guards the stacks for
   non-BMP.
5. **Newline translation on file reads** (latent, cheap to guard). Python's
   `open(..., 'r')` (python_inference.txt:1574) does universal-newline
   translation — `\r\n` and lone `\r` become `\n` on read; node's
   `fs.readFileSync(..., 'utf-8')` reads raw. Verified: zero `\r` bytes in
   any current source or artifact, so it cannot fire today — but a single
   `[return]` literal reaching an intermediate file would make the two
   chains read *different strings from the same bytes*. `jsself`
   grep-guards for `\r` alongside the non-BMP check.
6. **`Map` has no useful string form.** Anywhere a dictionary is
   stringified, Python prints `{...}` and JS prints `[object Map]`. With
   `.elems` off this is error/debug paths only — a known place a cosmetic
   diff could appear, not a correctness risk on the green path.
7. **Environment.** Record the node version (v22.22.2 today) next to the
   Python pin in `galenv`. Recursion: the Python artifacts never raise
   `setrecursionlimit`, so the default 1000-frame budget suffices — node's
   stack is comfortably deeper; `node --stack-size=…` is the escape hatch.

## Debugging protocol (when a stage diff is non-empty)

1. The failing (artifact, stage) pair gives one input file and two
   binaries: `python ${stage}_33.py in outA` vs `node ${stage}.js in outB`.
   **First check: grep the JS-side output for `NaN` and `undefined`** —
   the two silent-poison values (risk register #1) announce themselves in
   the bytes long after the cause.
2. For fallback divergence, diff the retained `fb0/fb1/…` chains to find
   the first diverging *iteration*.
3. Shrink: feed the chain progressively smaller slices of the input source
   until the diff is a screenful, then read the generated JS for that
   element.
4. Fix in `javascript_inference.txt` (usually), `./galjsbuild`, re-run
   `./jsself <artifact>`.

## Open questions

All design decisions were settled on 2026-07-16, and revised the same day
after review (see the decision sections above: default super args = none,
enforced via synthesized ctors in JS/Python + migration audit; `super`
must be the first constructor statement; M1 before M2; dict reads are bare
`Map.get` — the rev-3 throwing helper was based on a false premise and is
**rescinded**; `.elems` gated by a source-level boolean). One
administrative item remains:

1. **Version stamp**: DECIDED (Erik, 2026-07-16) — the compiler-in-JS
   release is **3.1** (milestones 1 and 2 together).
