# Sideways inheritance: `class set`

*Chapter 6 of the gal3 compiler design documentation. Sources:
`gal3/compiler_base.txt` lines 1287–1322 (`Sideways_Class_Statement`,
`Class_Append_Statement`), lines 2057–2153 (`Infer_Ordering`,
`Splice_Class_Set`); the `<lang>_inference.txt` backend files (usage).*

## The problem it solves

The compiler's element classes are declared once, in `compiler_base.txt` and
the dialect. But their *behavior* is contributed by many independent concerns:
the fallback lowering of an `If_Statement` lives with the fallback stage, its
Python generator with the Python backend, its Go generator with the Go
backend, and so on — up to eight backends plus the fallback and gal emitters.
Putting all of that in one class body would fuse every backend into one file;
putting each backend's logic in its own class would fragment each construct
across a parallel hierarchy.

gal3's answer is **sideways inheritance**: any file can append members to an
already-declared class with a `class set` statement. A backend file is, in
essence, a long list of method grafts onto the element classes it knows how to
generate:

```gal
class set If_Statement
{
    method number Infer_Python
    {
        ...   // the Python-specific generator for if
    }
}
```

The class is declared *bare* in one place (name, ancestry, properties,
target-independent behavior); each concern then extends it "sideways" from its
own module. Membership is decided at compile time by splicing, not at runtime
by lookup chains.

## Mechanism: a two-inference handshake

Sideways inheritance is executed *by the inference pipeline itself*, in two
steps.

**Step 1 — `Infer_Appends` (#8) records the intent.** `class set` is an
ordinary dialect statement classified as `Class_Append_Statement`. Its
`Infer_Appends` override (`compiler_base.txt:1295`) resolves the target class
by name in the global class registry and queues its block's statements:

```gal
class Class_Append_Statement is Class_Statement
{
    property object Primary_Class;
    method number Infer_Appends
    {
        string Name ([my Class_Name].Get_Input);
        if (not (dexists [Statement_Class:Names] Name))
        {
            error "'class set' could not append to nonexistent class " Name;
        }
        object C = (dget [Statement_Class:Names] Name);
        my Primary_Class = C;
        ...
        for each S in [my Block Statements]
        {
            push [C.Appended_Statements] S;
        }
        return 1;
    }
}
```

Appending to a class that doesn't exist is a hard error — extension is
deliberate, never accidental class creation.

**Step 2 — `Infer_Ordering` (#9) performs the splice.** The statements are
physically moved, at the parse-tree level, from the `class set` block into the
primary class's block (`Compiler.Infer_Ordering` → `Splice_Class_Set`,
`compiler_base.txt:2057–2136`):

```gal
comment `execute sideways inheritance: move the statement parse elements
of each class set block into the primary class parse element, then
re-derive the flat element list so appended members precede their class
in dependency order. this makes single-pass bottom-up inference correct
for classes extended by class set.`;
```

After the move, `Derive_Elements` re-runs, so the post-order contract (chapter
4) is restored: the grafted methods now appear in the flat list *before* their
class, exactly as if they had been written inside it. Everything downstream —
variable registration, type inference, code generation — sees one merged class
and never knows the members arrived from elsewhere. In the generated Python,
the class simply *has* those methods.

Two boundary conditions worth noting:

- The splice moves only `Statement` children; stray tokens/comments stay
  behind (`compiler_base.txt:2125`).
- The primary class's `End_Position` is extended to cover the appended source
  span (`compiler_base.txt:1310`), keeping provenance honest.
- A known sharp edge (`gal3/CLAUDE.md`): class-`set` **property defaults on
  generated-only classes are silently dropped** — behavior grafts reliably;
  state should live with the original declaration.

## A whole sugar family lowers to it

`class set` is the primitive; three higher-level constructs are *defined as
lowerings onto it* (chapter 5), which is how most sideways inheritance in the
codebase is actually written:

| surface form | lowers to |
|---|---|
| `generate X { body }` (inside `generator Lang ...`) | `class set X { method flag Infer_<Lang> { body } }` |
| `handle X { body }` (inside `inference Name ...`) | `class set X { method flag Infer_<Name> { body } }` |
| `generator Lang Ancestor { ... }` | `class <Lang>_Generator is <Ancestor>_Generator` + the synthesized per-element driver loop |

In fallback output the machinery then *disappears*: the `class set` wrapper
emits nothing once its splice target is known, and the primary class re-emits
itself including its `Appended_Statements` — so by atomic form, grafted
methods are textually inside their classes, and the backends' generated
Python simply has them.

## How the codebase uses it

The build concatenates source layers (chapter 9): every artifact =
`compiler_base + compiler_dialect + ...inferences... + backend layer(s)`.
Sideways inheritance is what makes concatenation *compositional*:

- `fallback_inference.txt` grafts `Infer_Fallback` lowerings onto composite
  element classes.
- Each `<lang>_inference.txt` grafts that language's generators onto the same
  classes — `python_inference.txt` and its five mirrors are essentially
  parallel columns of `class set` blocks over one shared row of element
  classes.
- A plugin (chapter 11) is the same thing again: new declarations plus
  `class set` grafts, included into the build.

So a single element class like `If_Statement` is assembled from up to ~10
files, each contributing the methods for one concern, with no file ever
editing another.

## Conventional theory comparison

| aspect | conventional mechanism | gal3 `class set` |
|---|---|---|
| open classes | Ruby monkey-patching, C# partial classes, Objective-C categories, Kotlin/Swift extensions | same intent; executed as a compile-time parse-tree splice by the inference pipeline |
| cross-cutting concerns | AOP (AspectJ inter-type declarations) | method grafts per concern-file; no join-point language, just class names |
| expression problem | visitors (new ops, closed types) vs. subclasses (new types, closed ops) | both axes open: new types via dialect+class, new ops via a new `Infer_*` method grafted across files |
| language workbenches | JastAdd inter-type aspect declarations, Polyglot extensible passes | closest relatives; gal3 does it in-language, on the same element objects the compiler compiles |
| linking model | separate compilation + linker | source-layer concatenation + splice during inference #9 |

Framing points for the paper:

- **The expression problem is the right lens.** A compiler is the canonical
  expression-problem instance: constructs × operations (passes/targets).
  Conventional designs pick a diagonal (visitors or node methods) and pay on
  the other axis. `class set` + broadcast inferences keep both axes open, and
  the fixpoint build substitutes for the static guarantees that were given up.
- **Partial classes, but *ordered by inference*.** C# partial classes are
  merged by the compiler before anything else happens. gal3's merge is an
  inference step with a defined position (#9): late enough that classification
  has resolved what's being appended to, early enough that all semantic
  inference sees the merged class. The merge is itself expressed in the
  language being compiled — the mechanism is self-hosted like everything else.
- **"Sideways" is accurate**: no new subclass is created (contrast subclass-
  per-backend designs), so there is exactly one `If_Statement` class whose
  identity all stages share — `is a` checks, the classification dictionary,
  and the class-name registry all keep working without adapter layers.
