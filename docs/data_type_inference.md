# Inferring Data Type

In C, we have functions like 'printf' that require us to know the data type of each argument. Take the following gal example.

~~~gal
say "There are " X " out of " N " of the " Task " remaining.";
~~~

Here is how that might look in C.

~~~c
printf("There are %d out of %d of the %s remaining.\n", X, N, Task);
~~~

gal variables are typed, but in the compiler dialect the typing is loose to allow generators to impose a more-specific type. A 'number' might be 'double' or 'float' or 'DECIMAL' depending on the ouput context. gal also assumes that language-specific considerations come into play when doing casting or type conversions, and these are the responsibility of the output generators. 

For example, in MUMPS everything is a string and the runtime system takes the 'numeric interpretation' or the 'integer interpretation' of the string when needed. In Python, everything is variant and there is a possibility of data type errors when generating a string into a numeric context. In C, everything is strongly typed, and it's very important to know the data type of every language element. 

The Data Type inference is meant to solve this problem. After the program has been parsed and every langage element has been classified, after variable definition scopes have been defined, it should be possible to infer the data type of every language element. For example, a reference to a variable 'X' will occur inside a method or block variable context, so we can look at the surrounding variable context to determine how 'X' is defined. If it is an integer, then the Data Type inference can assign a property of the Token language element indicating that it is defined as an integer. 

There are two ways in which we need to know the data type.

* Definition - the `Data_Type` property should tell us the definitional data type of the language element. So `Task` is defined as a string, while `N` is defined as an integer. 

* Usage - the `Usage` property should tell us the data type that is being applied to the language element by the surrounding context. For example in the 'say' to 'printf' translation example given above, all of the arguments of the 'say' statement are being used as strings. 

If the `Data_Type` property is the same as the `Usage`, then usually no specific action is required by the generator. However if they are not the same, then in some cases the generator logic will need to perform a type cast or take other actions to ensure that the conversion is made. So in C, the `printf` function can use the `Data_Type` property to determine what to put in the format string, while the `+` operation might need to convert a string to a number. 

gal language elements are supposed to work even when there is a data type mismatch, to the extent practical. If the target language has a problem with that, then the behavior isn't defined by gal. But this is only a convention - if we wanted the compiler to generate a warning or error when there is a data type mismatch, then that would be a valid approach. The `Data_Type` and `Usage` properties would also come into play, in that case. 

Classification is critical in implementing the `Data_Type` inference. A numeric binary operation imposes a numeric `Usage` on its arguments, and it defines a numeric `Data_Type` on its return value. A string concatenation operation imposes string `Usage` on its arguments and string `Data_Type` on its return value. In most cases, the language element class knows both the usage and the data type. 

## Implementation status (2026-07-06)

Ported from gal2's `Data_Types.gal` into gal3 as `data_type_inference.txt` (in the zero stack) and extended; the reserved `Infer_Variables` and `Infer_Type` pipeline stubs are now live. The pieces:

* **Scopes first** (`Infer_Variables`, in `compiler_base.txt`): every element has `Get_Variable_Context` — it asks its parent, and scoping elements (`Function_Statement`, `Module_Statement`) return themselves, exactly like `Get_Module`. Declarations register their name and type in the enclosing context (the declaration verb names the type); plural declarations register every name; property declarations register on the owner class; functions register their parameters (later parameters ride in comma `Syntax_Tail`s, whose keyword is the type). `Lookup_Variable` resolves a name up the chain.
* **Definitional types**: literal tokens know themselves (quotes are string, numbers are integer or number by decimal point); operation and literal-syntax **result types are properties inside the dialect declarations** (the `Syntax_True` pattern — the same mechanism as operator precedence, since `class set` property defaults on dialect classes are silently dropped); variable references resolve through the context chain; `[my X]` resolves through the owner class's registered properties.
* **Usage**: the argument declarations already written in the dialect state what each statement imposes on each argument — `Declared_Usage` stamps those onto the actual arguments through the `Statement_Class:Names` registry, filtered to real type names (the declared vocabulary mixes types with roles). Variadic statements (`say`, `verbose`, `comment`, `flowerbox`, `error`, `append`) have hand handlers imposing string usage. Declaration values receive their declared type as usage.
* **Two engine details that cost debugging**: usage and definitional stamps must land on the *classification* object, not the parse element (arguments captured during top-down classification are parse elements — the same dual-object trap as the precedence bug); and `Walk_Element` now completes missing `Parent` links on every parent–child edge, with `Get_Variable_Context` consulting classifications on the way up, so expression-interior tokens can reach their enclosing method.
* **`Data_Type_Report`** on the compiler gives per-type counts and untyped-operation lists — the coverage-driven iteration tool.

The say-to-printf example works end to end on a probe program: in `say Message ' ' Total;` the `Total` token carries `Data_Type integer, Usage string` — exactly what a C generator needs to choose `%d` and convert. The inference is behavior-neutral (no generator consumes it yet): the nine-artifact self-hosting fixpoint holds byte-exact with it running in every compile.

Not yet covered: method return types at call sites (`Operation_Call`/`Operation_I` stay untyped until a method registry lands), `[my A B]` chains, iterate/for-each loop variables, and the same inference for the python side (pygal currently emits `variant` everywhere — this machinery is what will let it emit typed declarations).

## The three-target demonstration (2026-07-06)

`examples/typedemo.txt` deliberately raises the conversion issues, and `bin/typedemo_oracle.sh` compiles it to **Python, JavaScript and C** and requires byte-identical output. Before the inference had consumers, the same program crashed in Python (`TypeError: can only concatenate str`), silently computed `answer 428` in JavaScript (`'42' + 8` concatenates), and had no C target at all. Now all three print `answer 50`, each having done a different amount of type work from the same two properties:

| concern | Python | JavaScript | C |
|---|---|---|---|
| string operand in numeric operation | `int(Digits) + 8` (else TypeError) | `Number(Digits) + 8` (else `'428'`) | `atoi(Digits) + 8` (else no compile) |
| say with mixed arguments | f-string, free | template literal, free | `printf("…%d…%s…", …)` — format chars from each argument's `Data_Type` |
| number used as string (`append`) | f-string, free | template, free | `sprintf(buf + strlen(buf), "%g", …)` |
| declarations | untyped | `var` | `int` / `double` / `char[256]` from the declaration |

The conversion *width* is chosen by `Usage`: the surrounding `integer Answer = …` context makes Python pick `int()` over `float()` and C pick `atoi` over `atof` — both properties earning their keep in one expression.

The C side is `c_inference.txt` + `c_main.txt` → the **`galc` artifact** (tenth, wired into build/selfbuild/selfself): a deliberate proof-of-concept covering main-only programs with scalar declarations, `say`, `append`, `if`, and the arithmetic/comparison operations — everything else fails loudly. Because the fallback stage lowers to atomics before `galc` runs, the C generator only ever sees the atomic set, which is the whole architectural bet on why C stays tractable. The Python and JavaScript arithmetic generators gained `Python_Numeric_Infix` / `Javascript_Numeric_Infix`, converting only operands whose inferred type is definitely `string` — variant and unknown stay untouched, so existing programs are unaffected (fixpoint-verified).

**Making `+` honestly numeric had consequences upstream, all improvements.** pygal's milestone-1 lowering of Python's polymorphic `py +` to gal's `+` only worked because gal's `+` used to compile to Python's `+`; it now lowers by inferred type — `append` (true concatenation) when an operand is a string, numeric `+` otherwise — and *records its decision* as its own `Data_Type`, so the links of a chained `py +` resolve left-to-right within one bottom-up pass. That chain surfaced two latent generation bugs (the 12th of the initiative): the `Operation_Append` Python generator still re-enquoted its assembled body (each nesting level added an escape layer — the second appearance of the f-string double-escape family), and nested `append` operations must flatten into one segment list at generation, because embedding a finished f-string inside another f-string's braces is illegal before Python 3.12. All verified: ten-artifact fixpoint, the pygal/pygen/pylex oracles, and the three-target demo.


## The coverage report — and why it had never run (2026-07-19)

`Compiler.Data_Type_Report` (`data_type_inference.txt`, in a `class set
Compiler`) is the census this initiative always wanted: for the program
being compiled, how many elements carry each definitional type, how many
carry each usage, and which classification classes are still untyped —
the same coverage-driven shape as the unclassified-verbs report. It runs
from `Infer_Type` under `verbose`:

```bash
python3 -c "
import sys; sys.path.insert(0,'$HOME/.gal3'); sys.setrecursionlimit(100000)
import gal_33 as G
c = G.Gal_Compiler(); c.Initialize(); c.File_Name='examples/bank.txt'
c.Code='<undefined>'; c.Infer()
print(c.Data_Type_Report())"
```

```
DATA TYPE REPORT
definitional:
  string 11    integer 18   number 2    flag 1
  module 1     object 6     class 1
usage:
  string 17    class 3      variable 8  variant 2
  value 5      method 7     property 5  module 1    object 5
untyped operations:
```

**It had never executed, in any artifact, for as long as it existed.**
Two bugs kept it dark, and both are worth remembering:

1. A `dialect` and a `class` may share a name — the compiler stack has
   both `class Compiler` and `dialect Compiler` — and both registered in
   the same class-name registry, last one winning. So `class set
   Compiler` spliced this method into the *dialect*, where nothing emits
   it: absent from the atomic and from every artifact, silently. Python
   never noticed because the only call site is `verbose`-guarded. MUMPS
   noticed immediately, because a missing label is a link error, not a
   surprise at call time.
2. With that fixed, the method itself failed on first run: `dget` on a
   missing key *yields null rather than raising*, so the `forgive` around
   `Count = (dget Types DT)` never fired and left `Count` null. Counting
   idioms need a `dexists` guard, not a `forgive`.

Both are pinned by `gal3/bin/regress_oracle.sh`. The lesson for this
initiative is the one it keeps teaching: a diagnostic nobody runs is a
diagnostic nobody trusts — and the way to find out is to host the
compiler somewhere less forgiving than Python.
