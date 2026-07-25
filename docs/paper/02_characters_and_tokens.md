# Characters and tokens as first-class objects

*Chapter 2 of the gal3 compiler design documentation. Sources:
`gal3/compiler_base.txt` lines 219–531 (`Character`, `Token` and their
subclasses), lines 1907–1945 (`Infer_Characters`, `Infer_Tokens`).*

## The unusual decision

In gal3, **every character of the source text becomes a heap-allocated object**
with its own class, position, and doubly-linked neighbors. Lexing is not a
finite automaton over a character stream; it is a sequence of polymorphic
method calls on those objects. This is the single largest reason the compiler
is slow — and it is deliberate, because it makes the lexer extensible and
introspectable by exactly the same mechanism as every other stage of the
compiler.

## The Character class hierarchy

`Character is Element` — a character is a full language element, carrying the
same `Document`, `Start_Position`, `End_Position`, `Classification`, and
`Parent` properties as a statement or an expression (`compiler_base.txt:219`).
Beyond that it has:

```gal
class Character is Element
{
    property string Text;
    property integer Position;
    property object Next [null];
    property object Prev [null];
    ...
}
```

The subclass tree encodes lexical category *as type*:

```
Character
├── Char_Ident
│   ├── Char_Upper
│   └── Char_Lower
├── Char_Number
├── Char_Punct
│   └── Char_Comma
├── Char_Quote
└── Char_Ws
    ├── Char_Line
    └── Char_Tab
```

A class-method factory (`Character:Factory`, `compiler_base.txt:225`) inspects
one character of text and instantiates the right subclass — quotes (including
the full set of typographic quotes `"` `` ` `` `“` `”` `‘` `’` `'` `«` `»`
`‹` `›`), digits, comma, identifier characters split by case, whitespace split
into line/tab/other, punctuation, and a catch-all.

`Infer_Characters` (`compiler_base.txt:1907`) is the whole "scanner":

```gal
for N range 0 L
{
    C = (substring Text N 1);
    Char = (Character:Factory [self] N C);
    if (defined Prev)
    {
        Char.Prev = Prev;
        Prev.Next = Char;
    }
    push [my Characters] Char;
    Prev = Char;
}
```

One object per character, threaded into a doubly-linked list (`Prev`/`Next`).
The links matter: later stages peek at neighbors — e.g. deciding whether `-` or
`.` starts a number requires `[Char.Next] is a Char_Number`
(`compiler_base.txt:347`, `459`).

## Tokenization as object growth, not automaton states

A `Token` is also an `Element`. Tokenization (`Infer_Tokens`,
`compiler_base.txt:1931`) is a two-method protocol:

1. **`Append_Character`** — the *current token object* is asked whether it will
   absorb the next character. Each token class overrides this with its own
   growth rule; the base class refuses everything (`compiler_base.txt:387`).
2. **`Token:Factory`** — when the current token refuses, a factory inspects the
   character (and its `Next` neighbor) and instantiates the right token
   subclass to start a new token (`compiler_base.txt:307`).

The driver is four lines:

```gal
for each Char in [my Characters]
{
    Status = (Current.Append_Character Char);
    continue if (Status > 0);
    Current = (Token:Factory Char);
    push [my Tokens] Current;
}
```

There is no lexer state machine, no token-kind enum, no regular expressions.
Where a conventional lexer encodes "an identifier is `[A-Za-z_][A-Za-z0-9_]*`"
as a DFA transition table, gal3 encodes it as a method on a class:

```gal
class Token_Word is Token
{
    method integer Append_Character [object Char]
    {
        if ((Char is a Char_Ident) or (Char is a Char_Number))
        {
            push [my Elements] Char;
            append [my Text] [Char.Text];
            my End_Position = [Char.End_Position];
            return 1;
        }
        return 0;
    }
}
```

The token subclass tree:

```
Token
├── Token_Word        absorbs ident/number chars
├── Token_Number      absorbs digits; one '.' if followed by a digit
├── Token_Boundary    { } [ ] ( ) ; — single-char, never grows
│   └── Token_Comma
├── Token_Punct
│   └── Token_Keyword operator/punctuation tokens
├── Token_Ws          absorbs non-line whitespace
│   ├── Token_Line    newline; never grows
│   ├── Token_Tab
│   └── Token_Spaces
└── Token_Quote       stateful: absorbs until the matching close quote
```

Two details show what the object representation buys:

- **`Token_Number`** (`compiler_base.txt:445`) accepts a `.` only if the token
  doesn't already contain one *and* the character's `Next` link is a digit —
  one-character lookahead expressed as pointer chasing on character objects,
  not as automaton lookahead.
- **`Token_Quote`** (`compiler_base.txt:506`) carries real state as properties:
  `Open`, `Open_Quote`, `Close_Quote`, `Unquoted`. The factory pairs
  typographic quotes (`“`→`”`, `«`→`»`, …), and `Append_Character` accumulates
  the `Unquoted` payload as a side effect of absorption. A string literal
  arrives at the parser already knowing its quote style and unquoted content.
  Note `property string Data_Type 'string'` — the token is *born typed*, and
  the data-type inference later reads it like any other element.

Tokens keep the character objects they absorbed: `push [my Elements] Char`.
Nothing is discarded. The finished token list is still, transitively, the
original text — every element in the final tree can recover its exact source
span via `Get_Input` (`compiler_base.txt:66`), which slices
`[my Document Text]` between `Start_Position` and `End_Position`.

## Why: uniformity over speed

The payoffs of making characters and tokens `Element`s:

1. **One mechanism everywhere.** Characters, tokens, expressions, statements,
   programs — all are `Element`s in one class hierarchy, all appear in the same
   flat post-order element list, and all respond to the same inference protocol
   (`Infer_Components`, `Infer_Gal`, `To_String`, …). A token *is* a leaf of
   the parse tree, not a separate pre-syntactic artifact. `Token.Infer_Gal`
   (`compiler_base.txt:425`) is `my Gal = [my Text]` — a token generates itself.
2. **Extension by subclassing.** Adding a lexical category is adding a class
   and a factory branch — the same move as adding a statement kind. No
   lexer-generator input file, no regeneration step.
3. **Full-fidelity provenance.** Positions, neighbor links, and retained
   character objects mean any later stage can ask "what text produced you?"
   without a side table. Error reporting (`Parser.High_Water`,
   `Element_Report`, `Error_Report`) rides on the same spans.
4. **Debuggability.** The compiler compiles to Python; the character and token
   objects are live Python objects that can be introspected in `zdebug` mid-
   compile. The lexer has no opaque state to reconstruct.

The cost is real and acknowledged: a megabyte of Python source becomes a
million linked `Character` objects before parsing even starts
("megabyte-scale parse time" is a known open item, `docs/status.md`). gal3
consciously trades constant-factor speed for architectural uniformity.

## Conventional theory comparison

| aspect | conventional lexer | gal3 |
|---|---|---|
| specification | regular expressions / lexer generator (lex, flex, re2c) or hand-written DFA | class hierarchy + per-class `Append_Character` methods |
| execution model | finite automaton over a char stream; O(1) memory per token | polymorphic dispatch per character; O(n) objects retained |
| token representation | (kind, lexeme, position) record; chars discarded | `Token is Element` object retaining its `Character` objects |
| lookahead | automaton lookahead / maximal munch | `Char.Next` pointer inspection |
| extensibility | edit grammar spec, regenerate | subclass + factory branch, same as any compiler extension |
| phase boundary | lexing is a separate phase with its own formalism (regular languages) | lexing is inference #2 and #3 of one uniform pipeline; no separate formalism |

Two framing points for the paper:

- **Dragon-book architecture separates lexing from parsing because regular
  languages admit a cheaper machine than context-free ones.** gal3 keeps the
  *phase* separation (characters → tokens → elements) but deliberately rejects
  the *formalism* separation: both phases are object construction driven by
  class dispatch. The theoretical efficiency argument for the split is
  abandoned in exchange for a single extension mechanism spanning the whole
  compiler.
- **Maximal munch appears as an object protocol.** The classical rule "the
  longest match wins" is exactly the `Append_Character`-until-refusal loop;
  each token class *is* the accepting-state logic of its own little automaton,
  but expressed as ordinary code that plugins and subclasses can override.
