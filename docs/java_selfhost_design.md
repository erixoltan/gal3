# gal3 Java toolchain — running the compiler on the JVM (3.2)

*Design document, 2026-07-18. Companion to
[js_selfhost_design.md](js_selfhost_design.md) (the 3.1 template this
follows), [architecture.md](architecture.md), and [status.md](status.md).*

## Decision

Java is the third compiler host, after Python (3.0) and JavaScript (3.1):
`gal.java`, `fallback.java`, `galpy.java`, `galjava.java` (and eventually the
rest), runnable under the JVM and rebuilding every artifact byte-identically.

Why Java before Go or C++: among the static targets it is the smallest
semantic jump from the two hosts that already work. Garbage collection makes
the cyclic element graph (parent pointers, shared mutation) a non-issue; real
inheritance and virtual dispatch match gal's class model directly; exceptions
map `forgive`/`error`/`try` naturally; `Object` + casts (with reflection as an
escape hatch) give a workable universal variant. The general static-typing
issues this port flushes out live in *shared* sources — solve them once here,
with JVM stack traces instead of Go type-system fights or C++ segfaults, and
the Go port (3.3, the native-single-binary distribution prize) inherits the
solutions and becomes mostly backend-local work. C++ follows; C# becomes a
cheap add once the Java backend is complete (near-mirror backend, then one
more self-host row).

## How this differs from the JS effort

The 3.1 port started from a **complete** backend; `galjava` is a **subset
backend** — built for the five-languages contract (hello, fizzbuzz, bank,
receipt, checkout) and designed to fail loudly beyond it. Promotion to full
coverage is the bulk of the work:

- `java_inference.txt` today: **61 generators**. `python_inference.txt`:
  **145**. Roughly **84 to port** (diff the `generate` lists to enumerate;
  the gap is dominated by `Operation_*` intrinsics, the statement family
  `Statement_Forgive`/`Try`/`Catch`/`Defined`/`Undefined`/`Super`/…, and the
  `Syntax_*` reference forms).
- `javascript_inference.txt` is the second complete example to consult when a
  Python body doesn't translate obviously; port bodies from
  `python_inference.txt` as the reference, per the established 1:1-mirror
  discipline.

The correctness bar is unchanged from 3.1: every artifact the Java compilers
produce is byte-identical to what the `_33` Python compilers produce from the
same input, at every pipeline stage. Bootstrap stays Python-only; Java grafts
onto the chain at the `_33` generation. The cheap-iteration property holds
here too: `java_inference.txt`/`java_main.txt` appear only in the galjava
source stack, so backend-only edits rebuild one artifact with the existing
fixpoint binaries — no full loop.

## Design notes for later (recorded 2026-07-18, from Erik)

These are principles to carry forward, not 3.2 work items.

1. **Compile-time inheritance flattening (the gal2 MUMPS approach).** The
   gal2 goalspell compiler had an Inheritance interface that resolved
   inheritance relationships at compile time and stamped out a fully-resolved
   MUMPS routine per class: if A inherits from B, every B method not
   explicitly overridden becomes a label in A's routine. The same approach is
   envisioned for gal3 targets **without a compatible inheritance mechanism —
   especially C** (it is a key piece of unfreezing `galc`), and MUMPS itself.
   It is an important step but a big one; Java's inheritance model is
   adequate, so 3.2 does not need it.

2. **Same outcomes, not same behavior.** gal never guarantees sameness across
   target languages — but the compiler shares one source across hosts and
   must work exactly the same way, so the **compiler dialect** at least must
   give identical outcomes. The technique when target behaviors diverge:
   introduce a *higher-level language element* and implement it differently
   per target. `undefined` is the model case — one language can check
   directly whether the thing is defined, another can attempt the access and
   catch the exception. Expect this port to mint more such elements; that is
   the intended mechanism, not a workaround.

3. **Typed member detail, two convergent routes (2026-07-18, mid-M1).**
   gal declares types but not object classes or structure member types —
   deliberately, since scripting targets don't need them and the rules
   differ across targets. For typed targets it is fine to (a) add optional
   declaration detail to gal source — e.g. a dictionary declared with
   string keys and element-classed values, a list with an element class —
   which targets like Java/C# consume and scripting targets simply ignore
   (candidate syntax: bracket detail after the keyword, `dictionary
   [Element] Class_Names;`, `list [Element] Statements;`, `property object
   [Element] Parent;`); and/or (b) extend the data-type inference to infer
   member classes and key/value types from use (generalizing the sibling
   scan the Java dictionary generator already does locally). Inference as
   the default source, declaration as the override where inference cannot
   see enough. This is what shrinks M1's reflective fallbacks into typed
   fast paths.

4. **Flexible fallback depth.** Today every element lowers all the way to
   atomic before target translation. But some targets can directly implement
   an element that *also* has a fallback lowering. As hosts and targets
   accumulate, the pipeline may need a per-target choice — "implement this
   element here, or keep lowering" — instead of always-to-atomic. Not needed
   yet; revisit when a concrete element wants it.

## Java-specific mappings to settle early

- **Variant**: `Object` + casts, steered by the existing data-type inference;
  where inference gives a definite type, emit it. The string-into-numeric
  conversion rules are already pinned (`Integer.parseInt`, a plain
  expression, no helper needed — see the backend header).
- **Dict semantics**: `HashMap` — must reproduce the Python backend's
  missing-key *outcome* (the 3.1 doc records the decision reversal; follow
  what the Python emission actually does, not `Map.get`'s null default).
- **AttributeError parity**: JS needed `Gal_New` proxies. Java fields are
  declared, so most probes resolve statically; where dynamic parity is
  genuinely needed, prefer a generated registry or a base-class helper over
  reflection-everywhere. This is prime territory for note 2 above
  (higher-level element, per-target implementation).
- **`defined` semantics**: gal3 backends compile an `is None`/`== null`
  check — keep Java on the `_3` semantics (null check), and remember the
  regime gotcha in gal3/CLAUDE.md.
- **Class/file mechanics**: one public class per file, file named after it —
  the oracle driver already handles this; artifacts stay single-file (public
  driver class + package-private siblings + the `Gal` helper class), which
  keeps the JDK 11+ single-file launcher (`java gal.java`) available during
  iteration, with `javac -Xlint:all -Werror` as the syntax gate.

## The iteration loop (in place, verified 2026-07-18)

- `./galjavabuild` — sibling of `galjsbuild`: rebuilds `galjava_33.py` alone
  with the fixpoint binaries, guarded against shared-source drift. Verified
  to reproduce the pre-existing binary byte-identically before any edits.
- Coverage probe: run each compiler atomic through the subset backend and
  census the fail-loudly errors —
  `python ~/.gal3/galjava_33.py ~/code/gal3build/<a>_33.atomic /dev/null`
  for `a` in `gal fallback galpy galjava`, grep `^ERROR`, `sort | uniq -c`.
- Contract regression gate: the five-languages oracle pointed at
  `galjava_33.py` instead of the bootstrap `galjava.py` (the stock oracle
  tests the gal2-built bootstrap, which goes stale during this loop).

## Milestones

- **M0 — baseline.** `bin/five_oracle.sh` java column green against current
  `_33`; snapshot ground truth. No source changes. **DONE 2026-07-18**
  (26/26).
- **M1 — generator promotion (backend-only, cheap loop).** Port the missing
  ~84 generators into `java_inference.txt`/`java_main.txt`, iterating per
  artifact: compile the compiler atomics (`gal`, `fallback`, `galpy`,
  `galjava`) to `.java`, gate with `javac -Xlint:all -Werror`. Done when all
  four atomics compile to javac-clean Java.

  **M1 DONE 2026-07-18** — all four self-hosting atomics generate with zero
  backend errors and compile javac-clean (JDK 21); five-languages oracle
  re-verified 26/26 throughout. What it took, beyond the generator ports
  (all backend-local, `./galjavabuild` cheap loop):
  - **The reflective access layer** (java's `Gal_New` analogue): a `galrt`
    runtime class (lowercase — gal names never are, so it cannot collide;
    a source variable literally named `Gal` forced the rename) with
    `get`/`set`/`call`/`call_static`/`create` via reflection, python
    attribute semantics (`Undefined` = AttributeError, `_attrs` map on the
    `GalBase` root for dynamic attributes), plus `truthy`/`num`/`len`/
    `each`/`contains`/`substring`/`split`/`join` for python-semantics
    primitives. Ancestor-less classes extend `galrt.GalBase`.
  - **Registries** built in one element-list walk (source text, *not*
    generated output — reading child `.Java` before generation poisoned
    return types): declared fields (`Cls.Prop` → java type), methods
    (→ return type + param list), ancestors, constructor signatures.
    Member access uses typed direct emission when declared, reflection
    otherwise.
  - **Structural translations**: local-variable *hoisting* (python
    function scoping vs java block scoping — declarations register on the
    enclosing function and emit as assignments, the function emits the
    typed declarations up top); loop/catch variables that are hoisted
    locals bind fresh names and assign; method return types resolve to the
    *topmost* same-named ancestor declaration (java override covariance),
    with value-dropping `return;` under a void ancestor and default
    returns for python fall-off; python's last-wins duplicate
    method/field definitions dedup per class; missing constructors
    synthesize ancestor pass-throughs; trailing argument defaults emit
    delegating overloads (defaulted params box, their default is null);
    class-name mangling (`Gal_` prefix) for String/Integer/Number/
    Character/List; `if (true) throw` defeats reachability analysis.
  - **Do-not-trust-the-inference rule**: probe variables (`string T
    [AC.Data_Type]` idiom) carry scalar inferences while holding elements,
    so string/list/dict data types never skip casts, `is a` receivers
    upcast to `(Object)`, containment always dispatches through the
    helper, and `==` between mixed flag/number goes numeric (python
    `False == 0`).
  - `@SuppressWarnings` on emitted classes keeps the `-Xlint:all -Werror`
    oracle gate green (javac wants explicit tokens, not "all").
  - First behavioral smoke test: `java Compiler_Program.java cptest.gal
    out` runs main → Infer → Infer_Input → Infer_Elements and stops at a
    reflective `Parse_Program` miss — that seam is where M2 starts.
  - Deferred shared-source item found along the way: gal's n-ary operation
    idiom `(A or B C)` parses, but the python backend's two-operand
    `Python_Infix` cannot emit it (`A or BC`); `(A or B or C)` instead
    treats the second `or` as an operand. Until the python/js and/or
    generators fold n-ary argument lists (the java backend already does),
    sources must nest: `((A or B) or C)`. `galjavabuild` now gates its
    output with `py_compile` so a generator bug cannot leave a stale
    binary silently passing downstream checks.

  *Progress 2026-07-18 — batch 1 landed (errors on the four atomics roughly
  halved, ≈16k → 8,154):* shared `Java_Append` concat builder extracted from
  Say/Append (now also behind `error`), `Java_String` coercion helper
  (fully-qualified `java.lang.String.valueOf` — compiler sources declare
  their own `String` class), and generators for `Statement_I`/`Operation_I`
  (this-calls), `Statement_Error`, `Statement_Debug` (throws, mirroring
  node), `Break`/`Continue`/`Forever`, `Increment`/`Decrement`,
  `Return_If`/`If_Return`, `Operation_Is_Null`/`Not_Null` (null-or-empty,
  matching Python's `in (None, "")`), `Operation_Is_A` (instanceof chain),
  `String_Equal`/`String_Not_Equal` (`.equals` over coerced operands),
  `Operation_List_Length`. Oracle re-verified 26/26 against the rebuilt
  `galjava_33`.

  *Next clusters, by census weight:* the **type map** (`Java_Type` for
  `object`/`list`/`dictionary`/`variant`, declarations without values,
  empty-list declarations, argument defaults — 1,497 + long tail); **mutable
  lists** (`List.of` → `ArrayList`, then `Statement_Push` 1,137,
  `Operation_Shift` 1,168, `Pop`/`List_Get`/`List_Copy`/`List_Split`);
  `Statement_Propset` 613; `Operation_Append` 325; `Statement_Forgive`/
  `Try`/`Catch` 304+; `Operation_Call` 262; and a real galjava bug:
  `'Syntax_List' object has no attribute 'Default_Value'` (207).
- **M2 — semantic parity (full loop when shared sources change).** Run the
  Java editions; chase behavioral divergences (dicts, variant, defined,
  string/number coercion). Any new higher-level elements or fallback changes
  land here, batched, with the fixpoint **and** `jsself` re-verified — the JS
  chain is now an independent verifier, exactly as 3.1 used the Python chain.

  **M2 substantially DONE 2026-07-18 (gal artifact row)** — the full Java
  chain `gal.java → fallback.java (4 passes to fixpoint) → galpy.java`
  reproduces the installed `gal_33.py` **byte-exactly** from `gal_33.tx2`
  (~9s for the 144KB parse under reflection vs 0.44s in python), and
  `galjava.java` emits byte-identical Java to the python-hosted backend
  (the java-built-java ≡ python-built-java seed of the java fixpoint).
  Fixpoint 13/13 and oracle 26/26 held throughout. Divergences found and
  fixed, in order:
  - **Field shadowing**: a subclass property re-declaration is a *second*
    java field; base-typed reads then hit the stale base field (python has
    one attribute). Re-declarations now emit instance-initializer
    assignments of the inherited field instead of fields.
  - **Field-type widening**: shadowing had hidden conflicting declared
    types in a chain (`property string Data_Type` above classes that store
    elements in it — the probe idiom). All conflicting chains widen to
    Object in the registry, and property emission reads the widened type.
  - **Undefaulted properties are None**: python materializes them as None
    (lists `[]`, dicts `{}`); java now emits null, boxing primitive
    property types so null fits. The definedness guards depend on this
    (the empty-Text bug: `"" != null` skipped the file read).
  - **Fall-off returns**: python's implicit `return None` passed a
    `Result = 0` check only because `None == 0` is False. One shared-source
    fix (explicit `return 1;` ending the `handle Compiler` block in
    attributes_inference.txt — full loop re-stamped, fixpoint clean).
  - **Counting-down ranges**: `for … by -1` emitted `<=` and never ran —
    Infer_Classification's reverse walk silently did nothing (the output
    still looked right because elements self-classify by default). The
    continuation test now flips on a negative literal increment.
  - **Dict ordering**: python dicts preserve insertion order; HashMap does
    not, and verb tie-breaking picked a different (legal) keyword form.
    All emitted dictionaries are now LinkedHashMap.
  - **str()-coercion trap in the backend itself**: probing
    `[AC.Unquoted]` through a `string` declaration coerces None to the
    text 'None' under the python host — repeat-count literals then merged
    as literal `None` into emitted java strings. Probe through an `object`
    variable (plain assignment, no coercion).

  **M2 COMPLETE for the minimal self-hosting set (2026-07-18, same day):**
  all four rows — `gal`, `fallback`, `galpy`, `galjava` sources — run
  through the all-Java chain (`gal.java` → `fallback.java` to fixpoint →
  `galpy.java`) with **byte-identical output at every stage** against the
  `_33` ground truth, and `galjava.java` emits byte-identical Java to the
  python-hosted backend. *Remaining for M3:* script it as `javaself`
  (mirroring `jsself`: staleness guard, per-stage diffs, install on
  green), then the remaining rows (`pylex`/`pyparse`/`pygen`, `pygal` the
  long pole).
- **M3 — `javaself`.** Sibling of `jsself`: emit all artifacts to `.java`,
  javac gate, run the Java chain out of `$BUILD`, diff every stage against
  `_33`; install into `~/.gal3/` only on green.

  **M3 DONE 2026-07-18** — `./javaself` exists (mirrors `jsself`: staleness
  guard, byte-hygiene guard including the shared UTF-16 non-BMP check, JDK
  21 pin, per-stage diffs, install-on-green). Java specifics: every
  artifact's public class is `Compiler_Program`, so phase A compiles each
  into its own work dir under `$BUILD/javaself/` — javac doubles as the
  gate and produces the runnable classes phase B uses (the fallback
  fixpoint runs an artifact 4-6 times; single-file launch would recompile
  every pass). The four chain rows are green at all stages including the
  java fixpoint, `.java` compilers installed; **all twelve artifact rows
  compile javac-clean**. Making the full matrix green surfaced one more
  structural batch, all backend-local:
  - **Op1/Op2 are the only real operands** of an operation — chains parse
    nested, and the flat `Arguments` list can carry a repeated operator
    keyword (`A and B and C` puts the second `and` there). The infix
    generators now mirror python/js strictly.
  - **A locals pre-pass in the registry walk** (params as `@param`,
    for-each/iterate/for-range variables typed by inference): generation
    is post-order, so a loop body generates before its loop statement —
    class-name-vs-local disambiguation (a local named `Element`!) and
    hoisting need locals known up front. Same-name different-type
    redeclarations (python one function-scoped var) widen to Object, with
    Object-widened locals converting at numeric/condition use sites.
  - Class-name heads in property chains access static fields directly
    (`Javascript_Browser_Compiler.Browser_Mode`), unless shadowed by a
    local; bare `return` in value-typed methods returns a default;
    `Java_Escape` handles carriage returns; quoted literals alone decide
    the leading-`""` concat rule; reflected code never skips casts.
- **M4 — the rest of the rows.** `pylex`/`pyparse`/`pygen`, then `pygal.java`
  (the long pole, as it was for JS), matching jsself's twelve rows.

## Known gap: a `[null]` argument becomes a null varargs array (2026-07-20)

`galrt.call` is `call(Object o, String name, Object... args)`, and the two
call generators (`java_inference.txt`, `generate Statement_Call` and
`generate Operation_Call`) append the argument list only when it is
non-empty — which is right. But when a call's *single argument* is gal's
`[null]`, the emitted Java is

```java
galrt.call(T, "Gal3_Expr", null)
```

and Java binds that `null` to the whole varargs **array**, not to one
element of it. Two things then go wrong at runtime: `call` computes
`args.length` with no null guard (NullPointerException), and even guarded
the arity would read as 0 where the source means 1, so the method would
not be found. Because such a call usually sits inside a `forgive`, the
failure would be swallowed and produce quietly wrong output rather than a
loud error — the same shape as the MUMPS `isa`-on-a-non-object bug.

javac says so itself, and names the fix: *"non-varargs call of varargs
method with inexact argument type for last parameter; cast to Object for a
varargs call."*

- **Fix:** when the generated argument list is exactly `null`, emit
  `(Object) null`. Add a null guard in `galrt.call` as defense in depth.
- **Where it bites:** three call sites, all from `pygal_base.txt`'s
  `(T.Gal3_Expr [null])`, so only in `pygal.java`.
- **Why the gate is still green:** `javaself` verifies the non-chain rows
  as compilation and java-fixpoint targets — it emits, javac-gates and
  rebuilds `pygal.java`, but never *runs* it on Python input. So this path
  is unexercised. It matters the day the Java edition of `pygal` is run,
  and it is worth fixing before then.
- Found 2026-07-20 by reading javac's warnings during a `javaself` run,
  not by a failing test. Pre-existing; unrelated to the 3.3 work.
