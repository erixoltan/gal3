# gal — the general abstract language

gal is a small programming language that compiles to six others. Write a
program once; the compiler gives you **Python, JavaScript, Go, Java, C++ or
MUMPS** source that does the same thing in each.

The compiler is written in gal. It rebuilds itself byte-for-byte, and it also
*runs* on four of its own targets: CPython, Node, the JVM and YottaDB.

> `gal` is always written lowercase — it stands for *general abstract
> language*.

## One program, six languages

This is FizzBuzz in gal. Names start with a capital letter, keywords are
lowercase, and a statement ends with a semicolon or a block.

```gal
module Fizzbuzz
{
    main
    {
        for range I 1 20
        {
            if ((I mod 15) = 0)
            {
                say "FizzBuzz";
            }
            else if ((I mod 3) = 0)
            {
                say "Fizz";
            }
            else if ((I mod 5) = 0)
            {
                say "Buzz";
            }
            else
            {
                say I;
            }
        }
    }
}
```

The gal 3.3 compiler turns that into real source for each target — unedited
compiler output:

```python
# module: Fizzbuzz
if __name__ == '__main__':
    for I in range(1,20+1):
        if I % 15 == 0:
            print('FizzBuzz')
        elif I % 3 == 0:
            print('Fizz')
        elif I % 5 == 0:
            print('Buzz')
        else:
            print(str(I))
```

```go
package main

import "fmt"

// module: Fizzbuzz
func main() {
	for I := 1; I <= 20; I++ {
		if (I % 15) == 0 {
			fmt.Println("FizzBuzz")
		} else if (I % 3) == 0 {
			fmt.Println("Fizz")
		} else if (I % 5) == 0 {
			fmt.Println("Buzz")
		} else {
			fmt.Printf("%d\n", I)
		}
	}
}
```

```java
@SuppressWarnings({"unchecked", "cast", "serial", "rawtypes", "this-escape", "deprecation", "removal"})
public class Fizzbuzz {
    public static void main(String[] args) {
        for (int I = 1; I <= 20; I++) {
            if (((I % 15) == 0)) {
                System.out.println("FizzBuzz");
            } else if (((I % 3) == 0)) {
                System.out.println("Fizz");
            } else if (((I % 5) == 0)) {
                System.out.println("Buzz");
            } else {
                System.out.println(I);
            }
        }
    }
}
```

```cpp
#include <iostream>

// module: Fizzbuzz
int main() {
    for (int I = 1; I <= 20; I++) {
        if ((I % 15) == 0) {
            std::cout << "FizzBuzz\n";
        } else if ((I % 3) == 0) {
            std::cout << "Fizz\n";
        } else if ((I % 5) == 0) {
            std::cout << "Buzz\n";
        } else {
            std::cout << I << "\n";
        }
    }
    return 0;
}
```

```javascript
// module: Fizzbuzz
// main program
for (var I = 1; I <= 20; I++)
{
    if (I % 15 == 0)
    {
        console.log('FizzBuzz');
    }
    else if (I % 3 == 0)
    {
        console.log('Fizz');
    }
    else if (I % 5 == 0)
    {
        console.log('Buzz');
    }
    else
    {
        console.log(globalThis.String(I));
    }
}
```

```mumps
Fizzbuzz ; gal ; Fizzbuzz module.
    do init^galrt
    do main()
    quit
main() ; main program
    new %etin set %etin=$etrap
    new $etrap,$estack set $etrap=%etin
    set I=1
    goto:$select(1<0:I<20,1:I>20) L41K
    goto L41B
L41C ; for range continue
    goto:$select(1<0:I+1<20,1:I+1>20) L41K
    set I=I+1
L41B ; for I range begin
    if ((I#15)=0)
    else  goto L80X
    use $principal write "FizzBuzz",!
    goto L80E
L80X ; if-else
    if ((I#3)=0)
    else  goto L173X
    use $principal write "Fizz",!
    goto L80E
L173X ; else-if-else
    if ((I#5)=0)
    else  goto L266X
    use $principal write "Buzz",!
    goto L80E
L266X ; else-if-else
    use $principal write I,!
L80E ; end if
    goto L41C
L41K ; for I range break
    quit
```

Every one of those programs prints the same twenty lines. The oracle that
proves it runs five programs through all targets and requires **byte-identical
output** from each.

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

That equality is the evidence: a compiler that reproduces itself exactly, from
a public seed, on your machine.

## The oracles

Two mechanical checks back the fixpoint — they are also the contribution gate
(see [CONTRIBUTING.md](CONTRIBUTING.md)):

```bash
gal3/bin/regress_oracle.sh                       # each case pins a fixed bug
GAL_ORACLE_LANGS=py,js gal3/bin/five_oracle.sh   # cross-target byte-identity
```

The full five-languages oracle (`gal3/bin/five_oracle.sh`, all backends)
requires `g++`, `go`, `javac`, and — for the MUMPS cells — YottaDB.

## What gal is like

- **A statement ends with a semicolon or a block.** `say "Hello, World!";`
  prints a line. `push List Value;` appends to a list.
- **Names are `Pascal_Case_With_Underscores`, keywords lowercase.**
- **One construct, one meaning.** A loop is `for range I 1 20` or
  `for each Item in Basket`; a dictionary read is `integer Price (dget Prices Item);`.
  No operator overloading, no implicit coercions to remember.
- **The pipeline is gal → fallback → target.** A high-level element lowers
  step by step into atomic gal, and per-language generators emit the target
  from the atomic result. Backends never parse original source.
- **Types are inferred per target.** gal is untyped at the source level; the
  compiler infers types so the generated Go, Java and C++ compile with their
  strictest flags.
- **gal source files are `.txt`** — only so editors stop trying to
  syntax-highlight them.

Try it in the browser at
**[generalabstractlanguage.com](https://generalabstractlanguage.com)** — the
site's playground and IDE run the compiler in the page.

## Experimental: reading Python into gal

gal3 also ships a toolchain that works the other direction: it parses
external Python into gal elements and translates it back out (`peg`,
`pylex`, `pyparse`, `pygen`, `pygal` — see `gal3/`). It is **experimental**,
a work in progress, and included as the public example of what
**[gal4](https://generalabstractlanguage.com/gal4/)** is for: reading programs
written in other languages into gal, and lifting low-level code back up into
more abstract code. Do not build on it yet.

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