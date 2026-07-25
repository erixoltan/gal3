# GAL3 Language Reference

## Overview
GAL3 is the third generation of the General Abstract Language compiler, featuring enhanced natural language syntax, a more modular architecture, and improved inference capabilities. This document serves as a comprehensive reference for implementing and using GAL3.

## Syntax Fundamentals

### Basic Structure
1. **Program**: A sequence of statements
2. **Statement**: A sequence of expressions terminating in a semicolon or block
3. **Expression**: An operation, syntax, or value token
4. **Operation**: Expressions surrounded by parentheses `(` and `)`
5. **Syntax**: Expressions surrounded by square brackets `[` and `]`
6. **Block**: Statements surrounded by curly braces `{` and `}`

### Tokens
1. **Names**: Begin with uppercase letter, colon `:`, dollar sign `$`, or underscore `_`
2. **Keywords**: Begin with lowercase letter or punctuation (except `{}()[]`)
3. **Numbers**: Numeric values
4. **Strings**: Text in quotes

## Compiler Architecture

### Inference Pipeline
GAL3 compiles code through a series of inference stages:

1. **Text Inference**: Load source code
2. **Character Inference**: Convert text to character objects
3. **Token Inference**: Combine characters into tokens
4. **Element Inference**: Parse tokens into language elements
5. **Component Inference**: Identify component structure in elements
6. **Classification Inference**: Classify elements into language constructs
7. **Attribute Inference**: Assign attributes to elements
8. **Append Inference**: Handle element relationships
9. **Ordering Inference**: Establish execution order
10. **Structure Inference**: Build hierarchical structure
11. **Variable Inference**: Identify and validate variables
12. **Type Inference**: Determine expression types
13. **Class Structure Inference**: Build class hierarchies
14. **Inheritance Inference**: Apply inheritance rules
15. **Code Inference**: Generate output code

### Core Classes

#### Element Classes
- **Element**: Base class for all language elements
- **Character**: Represents a single character in source code
- **Token**: Represents lexical tokens (words, numbers, punctuation)
- **Spell**: Base class for operations, statements, and syntaxes
- **Statement**: Language construct ending with semicolon or block
- **Operation**: Function-like construct in parentheses
- **Syntax**: Bracket-enclosed language construct
- **Block**: Group of statements in curly braces

#### Compiler Classes
- **Document**: Handles file reading/writing operations
- **Compiler**: Main class that manages compilation process
- **Parser**: Handles tokenization and parsing
- **Generator**: Creates output in target languages
- **Dialect**: Defines language variations and extensions

## Language Features

### Declarations
- **class**: Define a class with properties and methods
- **method**: Define a method within a class
- **property**: Define a class property
- **statement**: Define a statement language element
- **operation**: Define an operation language element
- **syntax**: Define a syntax language element

### Data Types
- **string**: Text data
- **integer**: Whole number
- **number**: Numeric value (float)
- **flag**: Boolean value
- **list**: Ordered collection
- **dictionary**: Key-value collection
- **object**: Instance of a class
- **variant**: Dynamic type for any value

### Control Flow
- **if/else**: Conditional execution
- **for each**: Iterate over collection
- **for range**: Iterate over number range
- **forever**: Infinite loop until break
- **break**: Exit loop
- **continue**: Skip to next iteration
- **return**: Exit method with value

### Error Handling
- **try/catch**: Exception handling
- **error**: Generate error
- **debug**: Enter debugger
- **verbosity**: Control debug output

## Dialect System
Dialects allow customizing language elements:

```
dialect MyDialect
{
    statements,
        Statement_WriteLine 'print' 'writeline',
        Statement_ReadLine 'input' 'readline';
    operations,
        Operation_Add '+' 'add',
        Operation_Subtract '-' 'subtract';
    syntaxes,
        Syntax_Self 'self' 'this';
}
```

## NSL Integration
The Natural Syntax Language (NSL) provides English-like syntax for GAL code, allowing more natural programming interfaces.

```
# NSL example
define a function that adds two numbers
    take first number and second number as parameters
    return the sum of first number and second number
```

## Generator System
Generators produce output in target languages:

```
generator Python
{
    generate Statement_WriteLine
        'print(' (i Python_Arguments) ')';
    
    generate Operation_Add
        '(' (i Python_First) ' + ' (i Python_Second) ')';
}
```

## Implementation Guidelines

### Completing the Inference Pipeline
1. **Append Inference**: Implement relationship building between elements
2. **Ordering Inference**: Establish execution order for statements/expressions
3. **Structure Inference**: Build hierarchical structure of program elements
4. **Variable Inference**: Identify variables and their scopes
5. **Type Inference**: Determine types of all expressions
6. **Class Structure**: Build class hierarchy and relationships
7. **Inheritance**: Apply inheritance rules to classes and methods
8. **Code Generation**: Generate output code based on inferred structure

### Testing Strategy
1. Create unit tests for each inference stage
2. Develop integration tests across multiple stages
3. Create end-to-end tests for complete compilation pipeline
4. Verify output against expected results in multiple target languages

## Example Programs

### Hello World
```
main
{
    writeline "Hello, World!";
}
```

### Function Definition
```
method integer Add [integer X, integer Y]
{
    return (+ X Y);
}
```

### Class Definition
```
class Person
{
    property string Name;
    property integer Age;
    
    constructor [string N, integer A]
    {
        my= Name N;
        my= Age A;
    }
    
    method string Description
    {
        return (append "Name: " [my Name] ", Age: " [my Age]);
    }
}
```

This document serves as a guide for implementing the GAL3 compiler, focusing on the inference pipeline and language features.

# Issues Unique to gal

## Perils of gal Compiler Work

In the below section, I will illustrate a common issue that causes confusion in gal compiler development. I present an example that we could use in the gal3 compiler to define the 'todo' statement, which is already present in gal1 and gal2. Inside that definition, I use a 'todo' statement. There is no problem including the 'todo' statement inside the definition of the 'todo' statement, because the code we write today will be compiled by the gal2 compiler, which already knows how to implement the 'todo' statement.

Then we are using the 'todo' statement in the gal2 code that defines the gal3 'todo' statement. If something goes wrong in compiling the 'todo' statement in our code, we ***must not*** make the mistake of modifying the gal3 definition of Statement_Todo to fix it. Instead, we must modify the gal2 version to fix it.

## Fallback Gal Generation

There are three kinds of spells, and I don't have a full naming or taxonomy of them. But 'atomic' spells can be generated directly into most other programming languages. Composite or fallback spells can be generated into 'fallback gal' code, which ultimately turns into atomic gal. I invented the term 'skycoding' when I invent highly abstract language elements that I don't know how to generate into fallback gal code, *yet*.

```gal
    integer X = 22;
    todo 'implement the following statement';
    pay Gratitude to Supporters of Person;
```

The first atomic line above might be Statement_Integer or Statement_Integer_Equal, depending on the dialect and what statement classes we implement. The second fallback line might be Statement_Todo and it could be generated into a Statement_Comment where the string "TODO:" is prepended to the comment text.

The third line might be a Statement_Pay_To_Of statement. That might be skycoding. It's not clear how to generate it into fallback logic. I might generate a debugger statement, so I could go into the debugger at that point and see what the situation is. Or it might throw an exception and Claude could help figure out what to do. Or I might develop an API call with a 'todo' statement in it, and compile it into an API invocation.

Here is an example of a statement spell with a fallback definition.

```gal
statement Todo 'todo' Comment
{
    todo 'Illustrate fallback capability';
    fallback '# "TODO: "' (i Fallback_Arguments) ';';
}
```

The 'fallback' statement is itself a fallback statement. Let's see what the above example might look like after fallback generation.

```gal
class Statement_Todo [is Comment_Statement]
{
    property string Keyword 'todo';
    comment "TODO: " 'Illustrate fallback capability';
    method void Infer_Fallback
    {
        string Code 'comment "TODO: "' (i Fallback_Arguments) ';';
        my Fallback = Code;
    }
}
```

And here it is in Python:

```python
class Statement_Todo (Comment_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'todo'
    # TODO: Illustrate fallback capability
    def Infer_Fallback(self):
        Code = 'comment "TODO: "' + str(self.Fallback_Arguments()) + ';'
        self.Fallback = Code
```

In gal2 the src/Fallback.gal module generates fallback gal code. This enables any complex language element to be translated into atomic gal. It is written in gal1 syntax, but I want to generate into gal2. We want the same capability in gal3, but written in updated gal2 syntax, and being generated into gal3 syntax.

## Sideways Inheritance

In goalspell gal2/src, Fallback.gal performs some sideways inheritance.

    - It generates fallback gal for Statement_Generator which creates a Gal_Generator class in gal.fallback, from the 'generator Gal ...' statement in gal.gal.

    - It generates fallback gal for Statement_Generate that creates a 'class set' which is a class append operation that should add an 'Infer_Gal' method to the Statement_Flowerbox code.

The purpose of 'sideways inheritance' is that I can have a barebones class structure in one module, and then use inferences or generators or 'class append' / 'class set' statements to add additional capabilities to the class later. Basically a new method is appended to the end of the class body. It's not smart enough to know if the class already has that method, unfortunately, in gal2.

So we could create a barebones dialect declaring statements and arguments in a module, and then have a python generator module define how to generate them into python, a gal module generate them into gal, etc. And the developers who write those modules will not have to alter the original dialect.

This is one way that programming language abstraction through the fallback process allows us to express ideas in code, that would be harder to express in a conventional programming language.

I have built a number of features on top of this sideways inheritance concept.

