# five languages: one gal program, five targets

Plan for the article / opening book chapter and accompanying video series:
five sample gal programs, each compiled to five very different programming
languages, all producing byte-identical output.

## the five languages

Chosen to span five distinct execution models, not just five syntaxes:

| language   | execution model            | how you run it            | backend status |
|------------|----------------------------|---------------------------|----------------|
| Python     | interpreter                | `python t.py`             | complete (self-hosting target) |
| JavaScript | JIT-ed dynamic engine      | `node t.js`               | complete (self-hosting target, 3.0.1) |
| C++        | native code, manual memory | `g++ t.cpp && ./t`        | **done 2026-07-12**: all five programs, byte-identical |
| Java       | managed bytecode VM        | `javac T.java && java T`  | **done 2026-07-12**: all five programs, byte-identical |
| Go         | native code with GC        | `go run t.go`             | **done 2026-07-11**: all five programs, byte-identical |

C# was considered and dropped (duplicates Java's point on the spectrum).
Rust dropped (borrow checker is the wrong fight for generated code).
C swapped for C++ 2026-07-12: gal-to-C means growing strings, collections
and object plumbing by hand — a real project of its own, future work —
while C++ keeps the native/manual-memory point on the spectrum and the
standard library carries the rest. The C proof of concept remains
(`c_inference.txt`, frozen; the oracle still runs its hello cell).

## the five programs

A ladder from trivial to the payoff. Every program is a task an
introductory programmer already recognizes — the output tells its own
story. The five programs together define the coverage contract: the C++,
Java and Go backends must handle exactly this subset and fail loudly
beyond it, per the c_inference.txt philosophy. Programs 3–5 share a
small commerce arc (bank account → receipt → checkout) for continuity.

One contract line to keep in mind when writing program six and beyond:
**programs never iterate a dictionary.** Iteration order differs per
target (Python/JS insertion order, Go deliberately randomized, Java
HashMap arbitrary, C++ std::map key-sorted), so a dict `for each` can
never be byte-identical. Receipt iterates the basket *list* and only
does `dget` lookups — that is the pattern.

1. **hello** — hello world inside a module. Already exists as
   `gal3/examples/example.txt`. Shows the module → package/class/file
   mapping, maximally different across the five targets (Java's class
   ceremony vs Go's `package main` vs C++'s bare `main()`).
2. **fizzbuzz** — the classic: count 1–20, Fizz on multiples of 3, Buzz
   on 5, FizzBuzz on 15. The most recognizable loop program there is.
   Exercises `for range`, `mod`, and an if/else chain.
3. **bank** — an `Account` class whose methods do real things: `Deposit`
   adds, `Withdraw` checks the balance and refuses an overdraft,
   `Statement` prints owner and balance. Main tells a story: deposit a
   paycheck, pay rent, get declined trying to overspend, print the
   statement. One class, no inheritance — keeps the C (struct +
   functions) and Go (struct + methods) mappings presentable.
4. **receipt** — print a store receipt: a `dict` price list (item →
   price), a `list` shopping basket, `for each` over the basket with
   `dget` lookups, string-built receipt lines, accumulated total.
5. **checkout** — the capstone: the data type inference demo reframed as
   the same shop's order form, where the quantity and coupon are typed
   in by the user via `readline` — input from the outside world really
   is a string. `string Quantity; readline 'how many boxes? ' Quantity;`
   then `number Subtotal (Quantity * Price);` becomes `int(...)`,
   `Number(...)` (without which JS charges $444), `std::stoi(...)`,
   `Integer.parseInt(...)`, `strconv.Atoi(...)` — one inference, five
   type systems, and the reader wrote none of them. The five input
   mechanisms are their own article beat: `input()` vs node fd-0 read vs
   `std::getline` vs `Scanner` vs `bufio.Scanner`. Derived from
   `gal3/examples/typedemo.txt` / `docs/data_type_inference.md`, already
   proven (hard-coded form) on Python/JS/C.

## readline (port from gal2)

Program 5 needs the gal2 `readline` statement, not yet in gal3. In gal2
it takes a mixed argument list — string literals are prompts, names are
variables each assigned one line of input (`readline '~ ' Input;`). The
fallback lowers it to `write <prompt>; <var> = (Runtime:Readline);`
(gal2 `Fallback.gal:2494`).

- gal3 work: add the dialect statement + fallback lowering.
- Python: `gal3/bin/Runtime.py` already has `Readline()` (= `input()`).
- JavaScript: gal2's `Runtime.js` uses browser-only `prompt()` — needs a
  node-compatible synchronous fd-0 stdin read.
- C++ / Java / Go: generators emit native reads — `std::getline`,
  `Scanner.nextLine()`, `bufio.Scanner`.

## backend work

Each new target follows the proven pattern: `<lang>_inference.txt` +
`<lang>_main.txt`, mirroring `python_inference.txt` structure (same
generate list, language-specific bodies), wired into `build`/`selfbuild`.
gal2 has a partial `src/Java.gal` target (~220 lines) to seed the Java
generators, alongside the proven Python.gal/Fallback.gal references.

- **Go first** (smaller language, no class hierarchy to fight, `gofmt`
  makes generated code presentable for free). Key decisions: module →
  `package main`, class → struct + pointer-receiver methods, list/dict →
  slice/map, say → `fmt.Println`.
- **Java second — done 2026-07-12** (`java_inference.txt` + `java_main.txt`
  → `galjava.py`). The mappings that landed: module → the public class
  holding `public static void main` (the output file carries the module's
  name, as javac demands); gal classes → package-private sibling classes
  in the same file (java's one-class-per-file rule only binds *public*
  classes); dict → `HashMap<String, T>` with T read from the first
  sibling `d=` value (the go trick, boxed); list → `List.of(...)`;
  say/append → `+` concatenation with literal runs merged into one
  quoted string and a leading `""` when the first piece isn't
  string-typed; string-in-numeric → inline
  `Integer.parseInt`/`Double.parseDouble` (no helper needed, unlike go);
  readline → a shared `Scanner` in a package-private `Gal` helper class
  appended at the end of the file; property defaults → field
  initializers (no constructor-placeholder machinery). Generated code is
  `javac -Xlint:all -Werror` clean; the for-each loop variable is `var`
  (the inference doesn't type it, and java can).
- **C++ third — done 2026-07-12** (`cpp_inference.txt` + `cpp_main.txt`
  → `galcpp.py`). Everything is `std::` qualified, no `using`. Objects
  live **on the stack**: `object Acct = (new Account 'Ada Lovelace');`
  becomes `Account Acct("Ada Lovelace");` — the one thing c++ shows that
  no other target can. Because gal objects are reference-typed and stack
  objects are value-typed, anything that would expose the copy fails
  loudly: assigning an object, passing one as an argument, returning
  one — all "outside the contract" errors, revisit with smart pointers
  when gal→c++ grows past the article subset. Other mappings: dict →
  `std::map<std::string, T>` (sibling-scan for T); list → `std::vector`
  brace-init; say → a `std::cout <<` chain with the newline folded into
  the trailing literal; append → `+` concatenation with
  `std::to_string` around numeric pieces; readline → `std::getline`
  inline (std::cin is tied to std::cout, prompts flush themselves);
  string-in-numeric → inline `std::stoi`/`std::stod`. No helper
  functions at all — the include-registry methodology at its purest.
  Generated code is `g++ -std=c++17 -Wall -Wextra -Werror` clean.
- **C extension — future work, out of scope for this initiative**: gal→C
  means hand-growing strings, collections and object plumbing (a real
  runtime design project). The POC stays frozen at hello
  (`c_inference.txt`); the oracle keeps its one c cell as a beachhead.

## the oracle

Extend `gal3/bin/typedemo_oracle.sh` into a five-by-five oracle: 5
programs × 5 languages = 25 cells, every program's five outputs required
byte-identical. For checkout, pipe fixed input (`printf '3\n5\n' | ...`)
to all five binaries — prompts count as output too. The oracle passing
IS the article's headline claim, and running it on camera is the money
shot of the video series (checkout gets typed live in the videos).

## article shape

1. Premise: one small language, five very different targets.
2. Program 1 side-by-side: five generated sources, five run commands,
   one output.
3. Programs 2–4 escalate; each section highlights one divergence
   (modules, control flow, objects, collections).
4. Program 5: the data type inference payoff.
5. Close: how the pipeline works (gal → fallback → target) and that the
   compiler compiles itself.

## videos

One video per program (five videos), each with the same beats: show the
gal source, compile to all five, cut between the five generated sources,
run all five, diff the outputs. Program 5's video ends with the full-matrix
oracle run.

## sequence

1. ~~Freeze the five programs~~ **DONE 2026-07-11.** All five live in
   `gal3/examples/`: `example.txt` (hello), `fizzbuzz.txt`, `bank.txt`,
   `receipt.txt`, `checkout.txt`. All five verified byte-identical on
   Python and JavaScript by `gal3/bin/five_oracle.sh` (the seed of the
   oracle: it whitelists implemented cells and grows columns as
   backends land). readline is in gal3 (dialect statement + Python
   `input(prompt)` + a node `Gal_Readline()` fd-0 helper emitted via the
   module include mechanism). Self-hosting fixpoint verified intact.
   Notes from the freeze: money is `integer` (whole-valued floats print
   `650.0` in Python vs `650` in JS); standalone class programs declare
   `class Base;` (the Python generator now gives an ancestor-less
   bodyless class an arg-sink `__init__`); `-` now converts string
   operands like `+ * / %` already did.
2. ~~Build the Go backend~~ **DONE 2026-07-11.** `gal3/go_inference.txt`
   + `go_main.txt` → `galgo.py`, wired into build/selfbuild/selfself; the
   oracle is 15/15 cells green. The mappings that landed: module →
   `package main` with a deduped import block; class → struct +
   `NewX(...)` + pointer-receiver methods (`class Base;` vanishes — go
   has no inheritance to chain to); dict → `map[string]T` with T
   inferred from the first sibling `d=` value; list → `[]T{...}`;
   say/append → `fmt.Printf`/`Sprintf` with a verb per inferred type
   (`%v` when untyped); string-in-numeric → `galAtoi`/`galAtof` helpers
   (strconv returns two values, so the conversion can't inline);
   readline → shared `bufio.Scanner` + `fmt.Print` prompts; `else`/
   `else if` merged onto the previous `}` by the Block generator; output
   piped through gofmt in the oracle. Imports and helper functions
   collect in class-level registries on Element because gal classes live
   outside the module. Shared-compiler improvements made for go: the
   for-range loop variable now registers as integer in the variable
   context (all targets benefit; C needs it too), and the go driver
   fails the compile when any element's generator errors (the C driver
   still silently continues — fix when extending C). Go toolchain:
   `~/.local/go` (1.26.5, arm64), added to PATH by `galenv`.
3. ~~Build the Java backend~~ **DONE 2026-07-12** (see backend work above).
4. ~~Build the C++ backend~~ **DONE 2026-07-12** (replaced the C
   extension, which moved to future work; see backend work above).
5. ~~Extend `five_oracle.sh` to the full 25 cells; make it pass~~
   **DONE 2026-07-12.** The oracle was green at 26 cells: the full 5×5
   matrix (py, js, cpp, go, java) plus the frozen hello×c cell. The
   java cell compiles with `javac -Xlint:all -Werror` and runs the
   classic `java <Module>` form; the cpp cell compiles with
   `g++ -std=c++17 -Wall -Wextra -Werror`. Both backends are wired into
   `build`/`selfbuild`/`selfself`.
   **Now 31 cells (2026-07-19):** MUMPS arrived as a sixth column after
   this initiative was scoped, so every program also runs under YottaDB
   with byte-identical output. The article stays a *five*-languages
   piece — the sixth is a choice for the writing, and if it earns a place
   the argument is that it is the one target with no objects, no separate
   collection types, and a database instead of a heap.
6. Draft the chapter from the oracle's artifacts.
7. Record the videos.
