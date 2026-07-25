# gal original concept

In 1987 I had a concept for a programming language, and the gal programming language is what eventually grew out of that concept. I want to talk about the original concept, how it relates to gal as it exists today, and what is still missing. My end goal in having this discussion is to add the missing part.

I learned about a 'decompiler' which was more of a myth than an actual software product at the time. There were obvious problems with the concept. Taking a machine language executable, a 'decompiler' would reverse-engineer the original source code. But it wouldn't know semantic variable names, would lose comments, and would only work for a specific compiler and source language.

## Transformation Rules

I hypothesized that these limitations were solvable. I saw that assembly language programs had an inherent structure, and that a low-level language could be developed to represent those structures using transformation rules.

~~~6502 assembly language
    LDA 0123
    STA 0145
~~~

A transformation rule could recognize a load and a store operation as an assignment statement. A transformation rule could recognize a previously-undeclared memory location as a definition statement. 1.

~~~generic assembly language
    define Z 0123;
    define Y 0145;
    Y = Z;
~~~

The name 'gal' originally stood for 'generic assembly language' and later came to mean 'general application language' and finally settled on either 'general abstract language' (because it could represent any program) or 'general altruistic language' (because I realized it was an AI program and I was worried about alignment).

## Bidirectional transformation rules

I was optimistic that an 'atomic' instruction set could be found that would represent the minimum set of instructions necessary to represent any program. And I was optimistic that a set of 'bidirectional' transformation rules could be developed, that would transform machine code into gal, and that would then generate gal from machine code. But neither of these hopes was realized.

Every programming language contains idiosyncratic instructions and has embedded code and assumptions that make the search for an atomic instruction set more of an academic than a practical initiative. It doesn't matter if there is a set of atomic instructions, what really matters is translating a Python program into C so it will run much faster. What matters is being able to take an old program that was written in a 'dead' language many years ago, and mine it for programming techniques that might solve some of the problems we are struggling with today.

So for gal I developed parse rules that were designed to make parsing much easier.

~~~gal
either Statement
    Scoped_Statement
    Line_Statement;

sequence Scoped_Statement
    [repeating Expression]
    '{'
    [optional repeating Statement]
    '}';

sequence Line_Statement
    [repeating Expression]
    ';';
~~~

These kinds of rules are reminiscent of BNF or PEG or many other syntax definition languages, but they are expressed in gal so they can be compiled by the gal compiler and generated into a program in any target language. I initially coded them as a recursive-descent parser even though I knew the performance might be problematic in the long run. I could see how the same syntax could be generated into other parser technologies, and the gal syntax was so simple that performance was adequate, so I stopped worrying about it while I struggled with the many other aspects of building a generic programming language that could be transpiled into many different target source languages.

Then to generate programs, I also used the gal syntax.

~~~gal

statement Assign '=' Line
{
    argument Variable 'variable' 'variable';
    argument Value 'variant' 'value';
    gal Variable ' = ' Value ';';
    fallback Variable ' = ' Value ';';
    mumps [indent] 'set ' Variable '=' Value [line];
    c Variable ' = ' Value ';';
    python Variable ' = ' Value;
}
~~~

These one-line generators can be simplified using the fallback process to a function that has a one-line concatenation statement.

~~~gal
method flag Infer_Mumps
{
    comment "mumps [indent] 'set ' Variable '=' Value [line];";
    string Variable [my Variable Mumps];
    string Value [my Value Mumps];
    string Code
        [indent] 'set ' Variable '=' Value [line];
    my Mumps = Code;
    return [true];
}
~~~

In many cases, it's muich more complicated to generate the output code for a language element. In those cases, the generator statement ('mumps', 'python', etc.) can have curly braces instead of a semicolon. The scoped statement form contains the full generator method body that is responsible for assigning the language property.

## Inferences

My early attempts at a gal compiler rejected object orientation -- I felt that a new way of thinking about programming was called for, one that went far beyond object oriented programming. This was an important step in my thinking, but eventually I went back to object orientation because it was already implemented and I realized it could be useful in the construction of the compiler.

A critical development came in gal version 2 (goalspell) when I realized that the parser and generator could be conceptualized as a series of inferences. I coded each inference as a completely separate step, operating on the current language representation.

There are two kinds of inferences: entity inferences and attribute inferences.

An `entity inference` operates on the current program and creates a new list of entities. So given the original source code as a string, a tokenization inference iterates character-by-character and produces a list of tokens. Or given a list of tokens, a parser inference uses the list of tokens and infers a list of language elements including tokens, syntaxes, operations and statements.

The most common and most important kind of inference is the `attribute inference`. An attribute inference iterates through a set of entities and adds a specific kind of attribute to those entities. The gal parser identifies statements, operations and syntaxes but doesn't classify them. So a classification inference determines that one statement is an assignment statement, another is a class statement and so on. The 'Classification' attribute is assigned.

Because the parser creates a list of elements in dependency order, the inferences can be run either left-to-right (bottom-up attribute inference) or right-to-left (top-down attribute inference). In a bottom-up inference, the child language elements have already performed the inference before their parent language element is operated upon. And in a top-down inference, the parent has done the inference before its children. This makes it possible to perform all the attribute inferences in a single pass.

## Abstraction Inference

In the current version gal3, the abstract inference rules are still missing. Such a set of rules would be a new kind of `entity inference`. Operating on a list of fully-classified and inferred language elements, the abstraction inference would create a new higher-level language element.

The first example of this was the 'assignment' example I gave earlier for assembly language. A load followed by a store is an assignment. In some ways, this is the opposite of a generator rule. Where a generator is expressing a higher-level language element by generating a sequence of lower-level instructions, an abstraction rule would search the program for a specific sequence of lower-level language elements and create a new higher-level language element to represent them.

In my original concept of gal, I hypothesized that a compiler would be able to 'grasp intent' by detecting a sequence of instructions and transforming them into a higher-level instruction. It would see the load followed by the store, and create an assignment operation. It would see a label followed by several statements and a conditional jump back to the label, and it would create a loop. I saw the possibility, but I didn't know how to make it work. Every idea I considered had serious drawbacks. I was constantly fighting against a combinatorial explosion.

Today we have large language models that can literally examine a source program and infer its meaning. A large language model can look at a sequence of instructions and grasp the fact that it is achieving a specific goal. The LLM has been trained on a very large number of programs and the accompanying explanatory text, and can write a text explanation describing the intent behind a program. So the problem of trying to understand the higher-level intent behind a sequence of instructions has already been solved.

To code such an entity inference, it would be necessary to describe a sequence of instructions and associate it with a higher-level language construct. It is useful to consider a lower-level language such as assembly language, but I have also used MUMPS as a low level language, so it's an alternative example. The MUMPS way of implementing structured programs is incompatible with many structured programming concepts. For example the argumentless 'do' statement and dot-block construct adds a stack level from which it is impossible to exit without a 'quit' that goes back to the point following the 'do'. You can't return from a function in the middle of a block. Therefore I have implemented 'if' / 'else' / 'for' / 'break' / 'continue' / 'return' statements with a flat-stack concept. The 'if' command (if it is false) uses a 'goto' statement to skip the block. The 'else' uses a GOTO in cases where the 'if' was not true. The 'for' uses a 'goto' at the end of the block, to go back to the start. The 'break' uses a 'goto' to jump to the end of the block, and the 'continue' uses a goto to jump back to the start. In assembly language a lot of the same spaghetti programming techniques are also used, but with a lower-level syntax.

An abstraction inference would search the code for patterns like the ones I mentioned above and convert them into corresponding higher-level language elements. It might be possible to reconstitute the 'if' and 'else' structure from a sequence of statements containing conditional 'goto' statements. It might be possible to reconstruct a 'for each' construct in the same way. Importantly, there are going to be cases where the lower level constructs do not add up to any well-defined higher level language elements. Those classes of cases need to be studied, because there are probably new kinds of higher-level language elements that we could invent to represent them, and such higher-level language elements might well be a useful addition to our existing programming constructs.

## Instruction Sequence Representation

To code this kind of abstraction inference, it would be necessary to develop some kind of notation or representation of a sequence of instructions that is flexible enough, and expressive enough, to represent the kinds of programming practices that are present in actual code. The representation would have to allow for arbitrary things to be in the middle, but it would have to exclude certain kinds of things. For example, and 'if' followed by an 'else' and 'end if' construct would have to allow a lot of different kinds of things to be inside the 'if' and 'else' blocks. But there would have to be limits to what those things could do. There might be 'forbidden' kinds of 'goto' statements that would represent a violation of the 'if' / 'else' / 'end if' construct. And it would need to be possible to next if/else structures inside other if/else structures, as well as loops, etc.

I'm not sure if there is a notation or a program syntax to use, or if an LLM should just analyze the code and try to convert it into a higher level program that could be generated into exactly the same output as the code we are looking at. So for example, given a target program with a lot of spaghetti programming constructs, an LLM could write the higher-level language elements to represent the same thing. If that code could be generated into exactly the same output logic, then we would consider it correct.

Alternatively, we could write an abstraction inference with code to automate the process of recognizing such higher-level language elements, and test the validity of the code using the same criteria. The rules are valid if the higher-level program can generate the same original lower-level code that the rules are transforming into a higher-level program.

## Status

This is not a fully-formed concept at this point. It is the 'missing component' of the original gal concept. I feel that we are in striking distance. I think we're at the point where this aspect of the gal concept could be added to the compiler, and then we would be getting much closer to a truly universal translation engine.
