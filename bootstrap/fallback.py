# module: Compiler
import string
import os
import sys
class Base:
    def __init__(self, A=None, B=None, C=None):
        pass

class Global:
    Class_Names = {} # class property dictionary

class Symbol:
    def __init__(self):
        self.Owner = None # object

class Flag(Symbol):
    def __init__(self, Object, Value=None):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # flag
        self.Symbol_Object = Object
        if Value is not None:
            self.Symbol_Value = Value

class Integer(Symbol):
    def __init__(self, Object, Value=None):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # integer
        self.Symbol_Object = Object
        if Value is not None:
            self.Symbol_Value = Value

class Number(Symbol):
    def __init__(self, Object, Value=None):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # number
        self.Symbol_Object = Object
        if Value is not None:
            self.Symbol_Value = Value

class String(Symbol):
    def __init__(self, Object, Value=None):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # string
        self.Symbol_Object = Object
        if Value is not None:
            self.Symbol_Value = Value

class Date(Symbol):
    def __init__(self, Object, Value=None):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # integer
        self.Symbol_Object = Object
        if Value is not None:
            self.Symbol_Value = Value

class List(Symbol):
    def __init__(self, Object):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = [] # list
        self.Symbol_Object = Object

class Dictionary(Symbol):
    def __init__(self, Object):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = {} # dictionary
        self.Symbol_Object = Object

class Entity(Symbol):
    def __init__(self, Object):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # object
        self.Symbol_Object = Object

class Variant(Symbol):
    def __init__(self, Object, Value=None):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # variant
        self.Symbol_Object = Object
        if Value is not None:
            self.Symbol_Value = Value

class Feature(Symbol):
    def __init__(self, Object, Value=None):
        super().__init__()
        self.Symbol_Object = None # object
        self.Symbol_Value = None # variant
        self.Symbol_Object = Object
        if Value is not None:
            self.Symbol_Value = Value

class Thing(Entity):
    pass
class Element:
    def __init__(self):
        self.Document = None # object
        self.Start_Position = None # integer
        self.End_Position = None # integer
        self.Classification = self # object
        self.Parent = None # object
        self.Variable_Context = None # object
        self.Error = '' # string
        self.Data_Type = '' # string
        self.Usage = '' # string
    def To_String(self):
        Text = f'{ self.__class__.__name__ } { self.Start_Position }-{ self.End_Position }'
        try:
            Text += f' gal { self.Gal }'
        except Exception: pass
        try:
            Text += f' fallback { self.Fallback }'
        except Exception: pass
        try:
            Text += f' python { self.Python }'
        except Exception: pass
        try:
            Elem = None
            for Elem in self.Elements:
                Text += f'{ self.Indent(Elem.To_String()) }\n'
        except Exception: pass
        return Text
    def Get_Input(self):
        Length = self.End_Position - self.Start_Position + 1
        Input = str(self.Document.Text[self.Start_Position:(self.Start_Position)+(Length)])
        return Input
    def Indent(self, Text):
        if (Text in (None, "")): return ''
        Qchars = '''"'`“‘«‹'''
        Qend = {}
        Qend['"'] = '"'
        Qend["'"] = "'"
        Qend['`'] = '`'
        Qend['“'] = '”'
        Qend['‘'] = '’'
        Qend['«'] = '»'
        Qend['‹'] = '›'
        P = None
        C = ''
        I = ''
        Quote = False
        Q = ''
        Between = ''
        E = len(Text) - 1
        if not Text[0] in Qchars:
            Between = '    '
        for P in range(0,E+1):
            C = Text[P]
            I += f'{ Between }{ C }'
            Between = ''
            if Quote:
                if C == Q:
                    Quote = False
                    Q = ''
            elif C == '\n':
                Between = '    '
            elif C in Qchars:
                Quote = True
                Q = Qend.get(C)
        return I
    def Enquote(self, Text):
        if not "'" in Text: return f"'{ Text }'"
        if not '"' in Text: return f'"{ Text }"'
        if not '`' in Text: return f'`{ Text }`'
        if not '“' in Text and not '”' in Text: return f'“{ Text }”'
        if not '‘' in Text and not '’' in Text: return f'‘{ Text }’'
        if not '«' in Text and not '»' in Text: return f'«{ Text }»'
        if not '‹' in Text and not '›' in Text: return f'‹{ Text }›'
        return "'ERROR goalspell compiler DEEPLY ENQUOTED STRING FAILED HERE'"
    def Infer_Appends(self):
        return 1
    def Get_Module(self):
        try:
            return self.Parent.Get_Module()
        except Exception: pass
        return None
    def Get_Variable_Context(self):
        # the enclosing element that owns variable definitions: an
        #         element does not know, so it asks its parent; elements that act as
        #         a variable context, such as methods, return themselves. a parse
        #         element consults its classification on the way up, because that is
        #         where the context behavior lives. the answer is cached on the
        #         element: every consumer runs after structure inference, when the
        #         parent chain no longer changes, and type inference asks often
        #         enough that the repeated walk dominates compile time.
        Cached = self.Variable_Context
        if not (Cached in (None, "")): return Cached
        try:
            C = self.Classification
            if not C == self:
                Ctx = C.Get_Variable_Context()
                if not (Ctx in (None, "")):
                    self.Variable_Context = Ctx
                    return Ctx
        except Exception: pass
        try:
            P = self.Parent
            Up = P.Get_Variable_Context()
            if not (Up in (None, "")):
                self.Variable_Context = Up
            return Up
        except Exception: pass
        return None
    def Lookup_Variable(self, Name):
        # resolve a variable name to its declared data type through
        #         the context chain; empty when nothing declares it. a context whose
        #         context is itself has no variable table on this path: answering
        #         empty here stops a self-recursion that would otherwise spiral to
        #         the recursion limit and be silently forgiven.
        try:
            Ctx = self.Get_Variable_Context()
            if (Ctx in (None, "")): return ''
            if Ctx == self: return ''
            return Ctx.Lookup_Variable(Name)
        except Exception: pass
        return ''
    def Type_From_Word(self, W):
        # translate a declaration or parameter keyword to the
        #         canonical type name it declares
        K = ' flag integer number string list dictionary object variant '
        if f' { W } ' in K: return W
        if W == 'dict': return 'dictionary'
        if W == 'var': return 'variant'
        if W == 'global': return 'list'
        if W == 'flags': return 'flag'
        if W == 'integers': return 'integer'
        if W == 'numbers': return 'number'
        if W == 'strings': return 'string'
        if W == 'objects': return 'object'
        if W == 'variants': return 'variant'
        if W == 'vars': return 'variant'
        if W == 'lists': return 'list'
        return ''
    def Register_Variables(self):
        pass
    
    def Get_Owner_Class(self):
        if isinstance(self.Classification, Class_Statement):
            return self.Classification
        try:
            return self.Parent.Get_Owner_Class()
        except Exception: pass
        return None
    def Get_Owner_Constructor(self):
        if isinstance(self.Classification, Statement_Constructor):
            return self.Classification
        try:
            return self.Parent.Get_Owner_Constructor()
        except Exception: pass
        return None
    def Attributes(self):
        pass
    
    def Next_Element(self, Next):
        # connect ifs to elses, etc.
        pass
    def Get_Innermost_Class(self):
        if self.Parent is not None:
            return self.Parent.Get_Innermost_Class()
        return None
    def Get_Variable_Context(self):
        if self.Parent is not None:
            return self.Parent.Get_Variable_Context()
        return None
    def Argument_Types(self, Type):
        # impose one usage type on every argument, for variadic
        #         statements such as say whose arguments are not declared
        Argument = None
        try:
            for Argument in self.Arguments:
                AC = Argument.Classification
                if str(AC.Usage) == '':
                    AC.Usage = Type
        except Exception: pass
    def Is_Type_Name(self, T):
        # the declared argument vocabulary mixes types with roles
        #         such as variable, value, class and method; only real types are
        #         stamped as usage, and variant imposes nothing
        K = ' flag integer number string list dictionary object '
        return f' { T } ' in K
    def Declared_Usage(self):
        # stamp the usage each argument declaration imposes onto
        #         the actual arguments, positionally, using the declaration this
        #         classification was generated from. keyword members are part of
        #         the verb and carry no argument position.
        try:
            Decl = Statement_Class.Names.get(self.__class__.__name__)
            Types = []
            M = None
            for M in Decl.Block.Statements:
                MC = M.Classification
                Wanted = False
                if isinstance(MC, Statement_Argument):
                    Wanted = True
                if isinstance(MC, Statement_Optional):
                    Wanted = True
                if not Wanted:
                    continue
                T = ''
                try:
                    TE = MC.Data_Type
                    T = TE.Get_Input()
                except Exception: pass
                Types.extend([T])
            N = len(self.Arguments)
            ND = len(Types)
            if ND < N:
                N = ND
            Sub = None
            End = N - 1
            for Sub in range(0,End+1):
                DT = str(Types[Sub])
                if not self.Is_Type_Name(DT):
                    continue
                Arg = self.Arguments[Sub]
                AC = Arg.Classification
                if str(AC.Usage) == '':
                    AC.Usage = DT
        except Exception: pass
    def Declare_Name_Type(self, Type):
        # a declaration statement gives its name the declared
        #         definitional type, and its initial value that usage
        try:
            N = self.Name
            NC = N.Classification
            NC.Data_Type = Type
        except Exception: pass
        try:
            if not (self.Value in (None, "")):
                V = self.Value
                VC = V.Classification
                if str(VC.Usage) == '':
                    VC.Usage = Type
        except Exception: pass
    def Infer_Intelligence(self):
        Verbose = True
        Target_Language = 'python'
        Class_Name = str(self.__class__.__name__)
        Input = str(self.Get_Input())
        Report = str(self.To_String())
        if Verbose:
            print('calling LLM COMPILE')
        # string Response (llm compile Target_Language Input Report);
        # verbose ’got python: ’ Response;
        # my Python = Response;
        return 1
    def Infer_Intelligence(self):
        Verbose = True
        Target_Language = 'python'
        Class_Name = str(self.__class__.__name__)
        Input = str(self.Get_Input())
        Report = str(self.To_String())
        if Verbose:
            print('calling LLM COMPILE')
        # string Response (llm compile Target_Language Input Report);
        # verbose ’got python: ’ Response;
        # my Python = Response;
        return 1
    def Infer_Attributes(self):
        return 1
    def Infer_Structure(self):
        pass
    
    def Infer_Data_Types(self):
        return 1
    def Infer_Inheritance(self):
        return 1
    def Infer_Fallback(self):
        Code = str(self.Gal)
        self.Fallback = Code

class Character(Element):
    def __init__(self):
        super().__init__()
        self.Text = None # string
        self.Position = None # integer
        self.Next = None # object
        self.Prev = None # object
    @classmethod
    def Factory(cls, O, P, C):
        # TODO: find out if it causes any problem to reference these before they are defined in the file.
        Char = None
        Q = '"`“”‘’'
        Q += "'«»‹›"
        if C in Q:
            Char = Char_Quote()
        elif C in '0123456789':
            Char = Char_Number()
        elif C == ',':
            Char = Char_Comma()
        elif C in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789":
            if C.isupper():
                Char = Char_Upper()
            elif C.islower():
                Char = Char_Lower()
            else:
                Char = Char_Ident()
        elif C in " \n\r\t":
            if C == str('\n'):
                Char = Char_Line()
            elif C == str('\t'):
                Char = Char_Tab()
            else:
                Char = Char_Ws()
        elif C == ',':
            Char = Char_Comma()
        elif C in string.punctuation:
            Char = Char_Punct()
        else:
            Char = Character()
        Char.Text = C
        Char.Start_Position = P
        Char.End_Position = P
        Char.Owner = O
        return Char

class Char_Ident(Character):
    pass
class Char_Upper(Char_Ident):
    pass
class Char_Lower(Char_Ident):
    pass
class Char_Number(Character):
    pass
class Char_Punct(Character):
    pass
class Char_Quote(Character):
    pass
class Char_Ws(Character):
    pass
class Char_Line(Char_Ws):
    pass
class Char_Tab(Char_Ws):
    pass
class Char_Comma(Char_Punct):
    pass
class Token(Element):
    def __init__(self):
        super().__init__()
        self.Elements = [] # list
    @classmethod
    def Factory(cls, Char):
        Tok = None
        Next = Char.Next
        C = str(Char.Text)
        if isinstance(Char, Char_Quote):
            Q = '"`“”‘’'
            Q += "'«»‹›"
            Tok = Token_Quote()
            Tok.Open_Quote = C
            if C == '-':
                import pdebug; pdebug.zbreak()
            if C == '“':
                Tok.Close_Quote = '”'
            elif C == '‘':
                Tok.Close_Quote = '’'
            elif C == '«':
                Tok.Close_Quote = '»'
            elif C == '‹':
                Tok.Close_Quote = '›'
            else:
                Tok.Close_Quote = C
        elif isinstance(Char, Char_Number):
            Tok = Token_Number()
        elif C in '-.' and isinstance(Next, Char_Number):
            Tok = Token_Number()
        elif isinstance(Char, Char_Ident):
            Tok = Token_Word()
        elif isinstance(Char, Char_Comma):
            Tok = Token_Comma()
        elif isinstance(Char, Char_Punct):
            if Char.Text in '{}[]();,':
                Tok = Token_Boundary()
            elif str(Char.Text) == '-':
                Tok = Token_Word()
            else:
                Tok = Token_Keyword()
        elif isinstance(Char, Char_Line):
            Tok = Token_Line()
        elif isinstance(Char, Char_Ws):
            Tok = Token_Ws()
        Tok.Text = C
        Tok.Start_Position = Char.Start_Position
        Tok.End_Position = Char.End_Position
        return Tok
    def Append_Character(self, Char):
        # by default, a token cannot append new characters
        return 0
    def To_String(self):
        Text = f'{ self.__class__.__name__ } { self.Start_Position }-{ self.End_Position } text { self.Text }'
        try:
            Text += f' gal { self.Gal }'
        except Exception: pass
        try:
            Text += f' fallback { self.Fallback }'
        except Exception: pass
        try:
            Text += f' python { self.Python }'
        except Exception: pass
        return Text
    def Infer_Components(self):
        return 1
    def Get_Input(self):
        return self.Text
    def Infer_Gal(self):
        self.Gal = self.Text
        return 1
    def Infer_Structure(self):
        pass
    
    def Infer_Gal(self):
        self.Gal = self.Text

class Token_Word(Token):
    def Append_Character(self, Char):
        if isinstance(Char, Char_Ident) or isinstance(Char, Char_Number):
            self.Elements.extend([Char])
            self.Text += str(Char.Text)
            self.End_Position = Char.End_Position
            return 1
        return 0
    def Infer_Data_Types(self):
        # a word token in an expression may be a variable
        #         reference: resolve its definitional type through the enclosing
        #         variable context chain
        if str(self.Data_Type) == '':
            try:
                T = str(self.Lookup_Variable(self.Text))
                if T > '':
                    self.Data_Type = T
            except Exception: pass
        return 1

class Token_Number(Token):
    def Append_Character(self, Char):
        if isinstance(Char, Char_Number):
            self.Elements.extend([Char])
            self.Text += str(Char.Text)
            self.End_Position = Char.End_Position
            return 1
        if str(Char.Text) == '.':
            if '.' in self.Text: return 0
            if not isinstance(Char.Next, Char_Number): return 0
            self.Elements.extend([Char])
            self.Text += str(Char.Text)
            self.End_Position = Char.End_Position
            return 1
        return 0
    def Infer_Data_Types(self):
        if '.' in self.Text:
            self.Data_Type = 'number'
        else:
            self.Data_Type = 'integer'
        return 1
    def Infer_Gal(self):
        Code = str(self.Text)
        self.Gal = Code

class Token_Boundary(Token):
    pass
class Token_Comma(Token_Boundary):
    pass
class Token_Punct(Token):
    pass
class Token_Keyword(Token_Punct):
    pass
class Token_Ws(Token):
    def Append_Character(self, Char):
        if not isinstance(Char, Char_Ws): return 0
        if isinstance(Char, Char_Line): return 0
        self.Elements.extend([Char])
        self.Text += str(Char.Text)
        self.End_Position = Char.End_Position
        return 1

class Token_Line(Token_Ws):
    def Append_Character(self, Char):
        return 0

class Token_Tab(Token_Ws):
    def Append_Character(self, Char):
        return 0

class Token_Spaces(Token_Ws):
    def Append_Character(self, Char):
        return 0

class Token_Quote(Token):
    def __init__(self):
        super().__init__()
        self.Open = True # flag
        self.Open_Quote = None # string
        self.Close_Quote = None # string
        self.Unquoted = '' # string
        self.Data_Type = 'string' # string
    def Append_Character(self, Char):
        if not self.Open: return 0
        self.Elements.extend([Char])
        self.Text += str(Char.Text)
        self.End_Position = Char.End_Position
        if str(Char.Text) == str(self.Close_Quote):
            self.Open = False
        else:
            self.Unquoted += str(Char.Text)
        return 1
    def Infer_Fallback(self):
        Code = str(self.Enquote(self.Unquoted))
        self.Fallback = Code

class Program(Element):
    def __init__(self):
        super().__init__()
        self.Statements = [] # list
    def To_String(self):
        Elem = None
        Text = f'{ self.__class__.__name__ } { self.Start_Position }-{ self.End_Position }\n{{\n'
        try:
            Text += f'    gal { self.Gal }\n'
        except Exception: pass
        try:
            Text += f'    fallback { self.Fallback }\n'
        except Exception: pass
        try:
            Text += f'    python { self.Python }\n'
        except Exception: pass
        for Elem in self.Elements:
            Text += f'{ self.Indent(Elem.To_String()) }\n'
        Text += '}'
        return Text
    def Infer_Components(self):
        self.Statements = self.Elements
        return 1
    def Infer_Gal(self):
        Code = ''
        Stmt = None
        for Stmt in self.Statements:
            try:
                if (Stmt.Gal in (None, "")):
                    Stmt.Infer_Gal()
            except Exception:
                import pdebug; pdebug.zbreak()
                Stmt.Infer_Gal()
            Code += f'{ Stmt.Gal }\n'
        self.Gal = Code
        return 1
    def Infer_Gal(self):
        Code = ''
        Stmt = None
        for Stmt in self.Statements:
            try:
                if Stmt.Gal is None:
                    raise ValueError
            except (ValueError, AttributeError):
                Stmt.Infer_Gal()
            Code += f'{ Stmt.Gal }\n'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = ''
        Stmt = None
        for Stmt in self.Statements:
            try:
                if Stmt.Fallback is None:
                    raise ValueError
            except (ValueError, AttributeError):
                Stmt.Infer_Fallback()
            Code += f'{ Stmt.Fallback }\n'
        self.Fallback = Code

class Spell(Element):
    def __init__(self):
        super().__init__()
        self.Elements = [] # list
        self.Keyword = None # string
        self.Keywords = [] # list
        self.Key_Words = [] # list
        self.Words = [] # list
        self.Arguments = [] # list
        self.Listargs = [] # list
        self.Dialect = None # object
    def To_String(self):
        Elem = None
        Text = f'({ self.__class__.__name__ } { self.Start_Position }-{ self.End_Position }'
        if self.Classification is not None:
            Text += f' is { self.Classification.__class__.__name__ }'
        Text += str('\n')
        try:
            Text += f"{ self.Indent(f'gal { self.Gal }') }\n"
        except Exception: pass
        try:
            Text += f"{ self.Indent(f'fallback { self.Fallback }') }\n"
        except Exception: pass
        try:
            Text += f"{ self.Indent(f'python { self.Python }') }\n"
        except Exception: pass
        Text += '    elements\n'
        for Elem in self.Elements:
            Text += f'{ self.Indent(Elem.To_String()) }\n'
        Text += ')'
        return Text
    def Create(self, Elem):
        Obj = self.__class__()
        Obj.Document = Elem.Document
        Obj.Start_Position = Elem.Start_Position
        Obj.End_Position = Elem.End_Position
        Obj.Keywords = Elem.Keywords
        Obj.Key_Words = Elem.Key_Words
        Obj.Verb = Elem.Verb
        return Obj
    def Classify_As(self, C):
        self.Classification = C
        E = None
        EC = None
        for E in self.Elements:
            C.Elements.extend([E.Classification])
        for E in self.Arguments:
            C.Arguments.extend([E.Classification])
        for E in self.Listargs:
            C.Listargs.extend([E.Classification])
    def Gal_Arguments(self):
        Code = ''
        Arg = None
        for Arg in self.Arguments:
            if isinstance(Arg, Statement_Tail):
                Code += str(Arg.Gal)
            else:
                Code += f' { Arg.Gal }'
        return Code
    def Gal_Args(self):
        Code = ''
        Arg = None
        for Arg in self.Listargs:
            if isinstance(Arg, Statement_Tail):
                Code += str(Arg.Gal)
            else:
                Code += f' { Arg.Gal }'
        return Code
    def Fallback_Arguments(self):
        Code = ''
        Arg = None
        for Arg in self.Arguments:
            Code += f' { Arg.Fallback }'
        return Code
    def Fallback_Args(self):
        Code = ''
        Arg = None
        for Arg in self.Listargs:
            Code += f' { Arg.Fallback }'
        return Code
    def Append_Fallback_Args(self):
        if len(self.Listargs) > 1:
            return ''
        Code = ''
        Arg = None
        for Arg in self.Listargs:
            Code += f' { Arg.Fallback }'
        if len(self.Listargs) > 1:
            return f' (append { Code })'
        return Code
    def Fallback_Memo_Wrapper(self, Rule_Name):
        # body of the packrat wrapper emitted around every generated
        #         parse rule. it consults the memo table keyed by token position and
        #         rule name, replays a cached outcome, or plants an in-progress seed and
        #         runs the real rule body (renamed with the _Rule suffix) against a
        #         fresh list. if the body reached its own seed, the rule is left
        #         recursive: re-run it while the match keeps growing, replaying the
        #         previous iteration at the recursion point and invalidating dependent
        #         memo entries each round. replayed elements are the same objects, so
        #         the element tree is identical to a fresh parse.
        W = f'string Memo_Key (append (string [my Token_Pos]) ":{ Rule_Name }");\nobject Memo_Hit (i Memo_Get Memo_Key);\nif (not (Memo_Hit is null))\n{{\n    return (i Memo_Replay Memo_Hit Parent_Elements);\n}}\ninteger Memo_Start_Token [my Token_Pos];\ninteger Memo_Start_Char [my Char_Pos];\nobject Memo_Seed (i Memo_Plant Memo_Key);\nlist Memo_Produced;\nflag Memo_Result (i Parse_{ Rule_Name }_Rule Memo_Produced);\ni Memo_Settle Memo_Seed Memo_Result Memo_Produced;\nif ([Memo_Seed.Detected] and Memo_Result)\n{{\n    forever\n    {{\n        i Memo_Regrow_Begin Memo_Seed;\n        my Token_Pos = Memo_Start_Token;\n        my Char_Pos = Memo_Start_Char;\n        list Memo_Grow;\n        flag Memo_Grow_Result (i Parse_{ Rule_Name }_Rule Memo_Grow);\n        break if (not (i Memo_Grew Memo_Seed Memo_Grow_Result Memo_Grow));\n    }}\n}}\ni Memo_Finish Memo_Seed;\nreturn (i Memo_Replay Memo_Seed Parent_Elements);\n'
        return W
    def Fallback_Arg_Data_Type(self, Arg):
        # an argument’s inferred definitional type, read through
        #         its classification; empty when unknown
        try:
            AC = Arg.Classification
            T = str(AC.Data_Type)
            if isinstance(T, Element): return ''
            return T
        except Exception: pass
        return ''
    def Infer_Structure(self):
        Arg = None
        for Arg in self.Arguments:
            Arg.Parent = self
            try:
                if Arg.Dialect is None:
                    raise ValueError
            except (ValueError, AttributeError):
                Arg.Dialect = self.Dialect
    def Infer_Data_Types(self):
        self.Declared_Usage()
        return 1

class Block(Element):
    def __init__(self):
        super().__init__()
        self.Statements = [] # list
        self.Gal_Statements = None # string
        self.Fallback_Statements = '' # string
    def To_String(self):
        Text = f'{ self.__class__.__name__ } { self.Start_Position }-{ self.End_Position }\n'
        try:
            Text += str(self.Indent(f'gal { self.Gal }\n'))
        except Exception: pass
        try:
            Text += str(self.Indent(f'fallback { self.Fallback }\n'))
        except Exception: pass
        try:
            Text += str(self.Indent(f'python { self.Python }\n'))
        except Exception: pass
        try:
            Elem = None
            for Elem in self.Elements:
                Text += f'{ self.Indent(Elem.To_String()) }\n'
        except Exception: pass
        return Text
    def Infer_Components(self):
        Elem = None
        for Elem in self.Elements:
            if isinstance(Elem, Token_Punct) and Elem.Text in '{}':
                continue
            if isinstance(Elem, Statement):
                self.Statements.extend([Elem])
        return 1
    def Infer_Gal(self):
        Statements = ''
        Line = None
        for Line in self.Statements:
            Statements += f'{ Line.Gal }\n'
        Code = ''
        if Statements == '':
            Code = ';'
        else:
            Statements = self.Indent(Statements)
            Code = f'\n{{\n{ Statements }}}'
        self.Gal_Statements = Statements
        self.Gal = Code
    def Infer_Fallback(self):
        Statements = ''
        Line = None
        for Line in self.Statements:
            Statements += f'{ Line.Fallback }\n'
        Code = ''
        if Statements == '':
            Code = ';'
        else:
            Statements = self.Indent(Statements)
            Code = f'\n{{\n{ Statements }}}'
        self.Fallback_Statements = Statements
        self.Fallback = Code

class Line(Spell):
    def Infer_Components(self):
        Args = self.Elements.copy()
        self.Arguments = Args
        Largs = Args.copy()
        self.Listargs = Largs
        return 1

class Statement(Spell):
    def __init__(self):
        super().__init__()
        self.Block = None # object
        self.Fallback_Declaration = '' # string
    def Get_Language_Name(self):
        if not self.Parent is not None: return None
        return self.Parent.Classification.Get_Language_Name()
    def Get_Property_Name(self):
        if not self.Parent is not None:
            import pdebug; pdebug.zbreak()
        return self.Parent.Classification.Get_Property_Name()
    def Infer_Components(self):
        Args = self.Elements.copy()
        Last = Args.pop()
        if isinstance(Last, Block):
            self.Block = Last
        else:
            B = Block()
            B.Start_Position = Last.Start_Position
            B.End_Position = Last.End_Position
            self.Block = B
        self.Arguments = Args
        Largs = Args.copy()
        self.Listargs = Largs
        return 1
    def Classify_As(self, C):
        self.Classification = C
        E = None
        EC = None
        for E in self.Elements:
            C.Elements.extend([E.Classification])
        for E in self.Arguments:
            C.Arguments.extend([E.Classification])
        for E in self.Listargs:
            C.Listargs.extend([E.Classification])
        C.Block = Block()
        for E in self.Block.Statements:
            C.Block.Statements.extend([E.Classification])
        self.Block.Classification = C.Block
    def Gal_Block(self):
        Code = ';'
        try:
            Code = self.Block.Gal
        except Exception: pass
        return Code
    def Fallback_Block(self):
        try:
            if self.Block.Fallback is None:
                raise ValueError
            return self.Block.Fallback
        except (ValueError, AttributeError):
            pass
        return ';'
    def Fallback_Statements(self):
        try:
            if self.Block.Fallback_Statements is None:
                raise ValueError
            return self.Block.Fallback_Statements
        except (ValueError, AttributeError):
            pass
        return ''
    def Infer_Structure(self):
        try:
            self.Block.Parent = self
        except Exception:
            self.Block = Block()
            self.Block.Parent = self
        try:
            if self.Block.Dialect is None:
                raise ValueError
        except (ValueError, AttributeError):
            self.Block.Dialect = self.Dialect
        Elem = None
        for Elem in self.Arguments:
            try:
                if Elem.Dialect is None:
                    raise ValueError
            except (ValueError, AttributeError):
                Elem.Dialect = self.Dialect
            Elem.Parent = self
        Prev = None
        for Elem in self.Block.Statements:
            Elem.Parent = self
            try:
                if Elem.Dialect is None:
                    raise ValueError
            except (ValueError, AttributeError):
                Elem.Dialect = self.Dialect
            if Prev:
                # connect ifs to elses, etc. — on the
                #                 classifications, where Next_Else is consumed; the
                #                 element-level call stays for compatibility
                Prev.Next_Element(Elem)
                try:
                    Prev.Classification.Next_Element(Elem.Classification)
                except Exception: pass
            Prev = Elem
    def Infer_Gal(self):
        Verbose = False
        Verbose = 'gal statement: '
        Between = ''
        # debug if ([self] is a Statement_Module);
        # debug if ([self] is a Statement_Statement);
        Code = ''
        try:
            if self.Verb is None:
                raise ValueError
            Code += f'{ Between }{ self.Verb }'
            Between = ' '
        except (ValueError, AttributeError):
            pass
        Code += f'{ self.Gal_Arguments() }{ self.Gal_Block() }'
        self.Gal = Code
        # verbose ’~~~’ Code ’~~~’;
    def Infer_Fallback(self):
        Code = f'{ self.Verb }{ self.Fallback_Arguments() }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_Tail(Spell):
    def Infer_Components(self):
        Elem = None
        for Elem in self.Elements:
            if isinstance(Elem, Token_Boundary):
                continue
            self.Arguments.extend([Elem])
            self.Listargs.extend([Elem])
        return 1
    def Infer_Gal(self):
        Keys = ' '.join(self.Key_Words)
        Code = f', { Keys }{ self.Gal_Arguments() }'
        self.Gal = Code

class Operation(Spell):
    def Infer_Components(self):
        Elem = None
        for Elem in self.Elements:
            if isinstance(Elem, Token_Boundary):
                continue
            self.Arguments.extend([Elem])
            self.Listargs.extend([Elem])
        return 1
    def Infer_Gal(self):
        Keys = ' '.join(self.Key_Words)
        Code = f'({ Keys }{ self.Gal_Arguments() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Verb }{ self.Fallback_Arguments() })'
        self.Fallback = Code

class Unary_Operation(Operation):
    pass
class Binary_Operation(Operation):
    pass
class Append_Args_Operation(Operation):
    pass
class Repeating_Operation(Operation):
    pass
class Syntax(Spell):
    def Infer_Components(self):
        Elem = None
        for Elem in self.Elements:
            if isinstance(Elem, Token_Boundary):
                continue
            self.Arguments.extend([Elem])
            self.Listargs.extend([Elem])
        return 1
    def To_String(self):
        Elem = None
        Text = f'[{ self.__class__.__name__ } { self.Start_Position }-{ self.End_Position }'
        if self.Classification is not None:
            Text += f' is { self.Classification.__class__.__name__ }'
        Text += str('\n')
        try:
            Text += f"{ self.Indent(f'gal { self.Gal }') }\n"
        except Exception: pass
        try:
            Text += f"{ self.Indent(f'fallback { self.Fallback }') }\n"
        except Exception: pass
        try:
            Text += f"{ self.Indent(f'python { self.Python }') }\n"
        except Exception: pass
        Text += '    elements\n'
        for Elem in self.Elements:
            Text += f'{ self.Indent(Elem.To_String()) }\n'
        Text += ']'
        return Text
    def Syntax_Gal(self, Code):
        Text = f'[{ Code }]'
        return Text
    def Infer_Gal(self):
        Code = ' '.join(self.Key_Words)
        First = True
        Arg = None
        for Arg in self.Arguments:
            if First and isinstance(Arg, Syntax_Tail):
                Code = self.Syntax_Gal(Code)
                First = False
            Code += f' { Arg.Gal }'
        if First:
            Code = self.Syntax_Gal(Code)
        self.Gal = Code
    def Infer_Fallback(self):
        Code = str(self.Verb)
        First = True
        Arg = None
        for Arg in self.Arguments:
            if First and isinstance(Arg, Syntax_Tail):
                Code = self.Syntax_Gal(Code)
                First = False
            Code += f' { Arg.Fallback }'
        if First:
            Code = self.Syntax_Gal(Code)
        self.Fallback = Code

class Syntax_Tail(Syntax):
    def Infer_Gal(self):
        Keys = ' '.join(self.Key_Words)
        Code = f'{ Keys }{ self.Gal_Arguments() }'
        Code = self.Syntax_Gal(Code)
        self.Gal = Code
    def Infer_Fallback(self):
        Keys = ' '.join(self.Key_Words)
        Code = f'{ Keys }{ self.Fallback_Arguments() }'
        Code = self.Syntax_Gal(Code)
        self.Fallback = Code

class Literal_Syntax(Syntax):
    def __init__(self):
        super().__init__()
        self.Unquoted = None # string

class Argument_Syntax(Syntax):
    pass
class Dialect:
    def __init__(self):
        self.Keywords = {} # dictionary
        self.Elements = [] # list
        self.Statements = {} # dictionary
        self.Operations = {} # dictionary
        self.Syntaxes = {} # dictionary
        self.Unclassified_Verbs = {} # dictionary
    def Add_Keywords(self, Text):
        if ' ' in Text:
            Word = ''
            Words = Text.split(' ').copy()
            for Word in Words:
                self.Keywords[Word] = True
        else:
            self.Keywords[Text] = True
    def Choose_Class(self, D, Elem, Args, Largs):
        Verbose = True
        Elem.Arguments = Args
        Elem.Listargs = Largs
        V = ''
        Verb = ''
        Arg = ''
        Before = []
        This = []
        Bef = ''
        Blen = None
        Deepest = 0
        Candidates = {}
        # TODO: this is not perfect
        for Arg in Elem.Key_Words:
            This.clear()
            for Bef in Before:
                V = f'{ Bef } { Arg }'
                Blen = Candidates.get(Bef) + 1
                Candidates[V] = Blen
                This.extend([V])
            Before.extend([Arg])
            Candidates[Arg] = 1
            for V in This:
                Before.extend([V])
        for Arg, Blen in Candidates.items():
            if Arg in D and Blen > Deepest:
                Verb = Arg
                Deepest = Blen
        if Verb == '':
            Verb = ' '.join(Elem.Key_Words)
        Elem.Verb = Verb
        # verb identified, remove from arguments list
        Kw = Verb.split(' ')
        Arglst = []
        A = None
        Ignore = None
        for A in Args:
            if isinstance(A, Token):
                Arg = A.Text
                if len(Kw) > 0:
                    if Arg == str(Kw[0]):
                        Ignore = Kw.pop(0)
                        continue
            Arglst.extend([A])
        Elem.Arguments = Arglst
        La = Arglst.copy()
        Elem.Listargs = La
        if Verb in D:
            C = D.get(Verb)
            C = C.Create(Elem)
            if C == Elem:
                import pdebug; pdebug.zbreak()
            Elem.Classify_As(C)
            # verbose ’classified ’ [class C name] ”: ” Verb;
        else:
            import pdebug; pdebug.zbreak()
            if Verbose:
                print(f'UN classified { Elem.__class__.__name__ }: verb { Verb }')
            if Verbose:
                print(str(Elem.Get_Input()))
            # Trackunclassifiedverbstohelpwithdebugginganddevelopment
            if Verb in self.Unclassified_Verbs:
                Count = self.Unclassified_Verbs.get(Verb)
                self.Unclassified_Verbs[Verb] = Count + 1
            else:
                self.Unclassified_Verbs[Verb] = 1
            Elem.Classification = Elem
    def Print_Unclassified_Verbs(self):
        if not self.Unclassified_Verbs is not None:
            return ''
        Issues = False
        Report = ''
        Report += '=== UNCLASSIFIED VERBS ===\n'
        K = None
        Count = None
        for K, Count in self.Unclassified_Verbs.items():
            Report += f"Verb: '{ K }' (count: { str(Count) })\n"
            Issues = True
        Report += '==========================\n'
        if Issues: return Report
        return ''
    def Classify(self, Elem):
        Verbose = False
        # classify this element and its children
        D = None
        E = None
        if isinstance(Elem, Spell):
            T = ''
            Args = Elem.Arguments.copy()
            Largs = Args.copy()
            for E in Elem.Arguments:
                if isinstance(E, Token):
                    T = E.Text
                    if T in self.Keywords:
                        Elem.Keywords.extend([E])
                        Elem.Key_Words.extend([T])
                        continue
                    elif isinstance(E, Token_Word):
                        Elem.Words.extend([T])
                    elif isinstance(E, Token_Keyword):
                        Elem.Keywords.extend([E])
                        Elem.Key_Words.extend([T])
            if len(Elem.Key_Words) == 0 and len(Elem.Words) == 0:
                import pdebug; pdebug.zbreak()
                return 0
            if isinstance(Elem, Statement):
                self.Choose_Class(self.Statements, Elem, Args, Largs)
            elif isinstance(Elem, Operation):
                self.Choose_Class(self.Operations, Elem, Args, Largs)
            elif isinstance(Elem, Syntax):
                self.Choose_Class(self.Syntaxes, Elem, Args, Largs)
            elif isinstance(Elem, Line):
                self.Choose_Class(self.Statements, Elem, Args, Largs)
            else:
                Elem.Classification = Elem
                if Verbose:
                    print(f'SELF classified { Elem.__class__.__name__ }')
        return 1

class Line_Statement(Statement):
    pass
class Scoped_Statement(Statement):
    pass
class Comment_Statement(Line_Statement):
    pass
class Append_Args_Statement(Line_Statement):
    pass
class Declaration_Statement(Line_Statement):
    def Declared_Type(self):
        # the declaration verb names the type: integer X declares
        #         an integer. aliases such as dict translate to the canonical name,
        #         and forms like number = keep only the first word.
        V = str(self.Verb)
        W = ''
        P = 0
        L = len(V)
        while True:
            if P >= L:
                break
            C = str(V[P])
            if C == ' ':
                break
            W += C
            (P) += 1
        return self.Type_From_Word(W)
    def Register_Variables(self):
        try:
            Ctx = self.Get_Variable_Context()
            if (Ctx in (None, "")): return
            T = str(self.Declared_Type())
            if T == '': return
            N = self.Name
            Nm = str(N.Get_Input())
            Ctx.Variables[Nm] = T
        except Exception: pass
    def Infer_Gal(self):
        Name = str(self.Name.Gal)
        Value = ''
        try:
            if self.Value is None:
                raise ValueError
            Value += f' = { self.Value.Gal }'
        except (ValueError, AttributeError):
            pass
        Code = f'{ self.Keyword } { Name }{ Value };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'{ self.Keyword } { self.Name.Fallback }'
        try:
            if self.Value is None:
                raise ValueError
            Code += f' = { self.Value.Fallback }'
        except (ValueError, AttributeError):
            pass
        Code += ';'
        self.Fallback = Code

class Declarations_Statement(Line_Statement):
    def Register_Variables(self):
        # the plural form declares every listed name
        try:
            Ctx = self.Get_Variable_Context()
            if (Ctx in (None, "")): return
            V = str(self.Verb)
            T = str(self.Type_From_Word(V))
            if T == '': return
            N = None
            for N in self.Listargs:
                try:
                    Nm = str(N.Get_Input())
                    Ctx.Variables[Nm] = T
                except Exception: pass
        except Exception: pass

class Property_Statement(Declaration_Statement):
    def Register_Variables(self):
        # a property belongs to its owner class, not to a method
        #         scope; my references resolve against the class
        try:
            Cls = self.Get_Owner_Class()
            if (Cls in (None, "")): return
            T = self.Type
            TW = str(self.Type_From_Word(T.Get_Input()))
            if TW == '': return
            N = self.Name
            Nm = str(N.Get_Input())
            Cls.Variables[Nm] = TW
        except Exception: pass

class Function_Statement(Scoped_Statement):
    def __init__(self):
        super().__init__()
        self.Variables = {} # dictionary
        self.Parameters = {} # dictionary
        self.Variables = {} # dictionary
    def Get_Variable_Context(self):
        return self
    def Lookup_Variable(self, Name):
        if Name in self.Parameters:
            return self.Parameters.get(Name)
        if Name in self.Variables:
            return self.Variables.get(Name)
        try:
            P = self.Parent
            Ctx = P.Get_Variable_Context()
            if (Ctx in (None, "")): return ''
            return Ctx.Lookup_Variable(Name)
        except Exception: pass
        return ''
    def Register_Variables(self):
        # a function registers its own parameters: each bracketed
        #         parameter is a typed argument syntax whose keyword names the type.
        #         parameters after the first nest inside the previous one’s argument
        #         chain, so the walk follows each syntax’s extras.
        try:
            Work = []
            P = None
            for P in self.Listargs:
                Work.extend([P])
            while True:
                if len(Work) == 0:
                    break
                W = Work.pop(0)
                try:
                    PC = W.Classification
                    X = None
                    try:
                        for X in PC.Arguments:
                            Work.extend([X])
                    except Exception: pass
                    N = ''
                    T = ''
                    if isinstance(PC, Syntax_Tail):
                        # a later parameter rides in a comma tail:
                        #                         the type is its keyword, the name its argument
                        NV = PC.Arguments[0]
                        N = NV.Get_Input()
                        KW = str(PC.Key_Words[0])
                        T = self.Type_From_Word(KW)
                    else:
                        PV = PC.Variable
                        N = PV.Get_Input()
                        try:
                            T = PC.Data_Type
                        except Exception: pass
                        if isinstance(T, Element):
                            T = ''
                        if T == '':
                            T = self.Type_From_Word(PC.Keyword)
                    if N > '' and T > '':
                        self.Parameters[N] = T
                except Exception: pass
        except Exception: pass
    def Get_Variable_Context(self):
        return self

class Method_Statement(Function_Statement):
    def __init__(self):
        super().__init__()
        self.Variables = {} # dictionary
    def Get_Variable_Context(self):
        return self

class Sideways_Method_Statement(Method_Statement):
    pass
class Class_Statement(Scoped_Statement):
    def __init__(self):
        super().__init__()
        self.Variables = {} # dictionary
        self.Appended_Statements = [] # list
        self.Generate_Constructor = False # flag
        self.Variables = {} # dictionary
        self.Inheritance_Compiled = False # flag
        self.Compiled_Ancestors = {} # dictionary
        self.Compiled_Class_Properties = {} # dictionary
        self.Compiled_Class_Methods = {} # dictionary
        self.Compiled_Properties = {} # dictionary
        self.Compiled_Methods = {} # dictionary
        self.Compiled_Constructor = None # object
    def Get_Owner_Class(self):
        return self
    def Get_Innermost_Class(self):
        return self
    def Get_Variable_Context(self):
        return self
    def Inherit_Member(self, S):
        # files one member statement into the flattened tables;
        #         the specific class-member kinds test before their bases
        C = S.Classification
        MN = ''
        try:
            MN = C.Name.Get_Input()
        except Exception: pass
        if isinstance(C, Statement_Constructor):
            self.Compiled_Constructor = C
        elif isinstance(C, Statement_Class_Property):
            if MN > '':
                self.Compiled_Class_Properties[MN] = C
        elif isinstance(C, Statement_Class_Method):
            if MN > '':
                self.Compiled_Class_Methods[MN] = C
        elif isinstance(C, Property_Statement):
            if MN > '':
                self.Compiled_Properties[MN] = C
        elif isinstance(C, Method_Statement):
            if MN > '':
                self.Compiled_Methods[MN] = C
    def Inherit(self):
        if self.Inheritance_Compiled:
            return 1
        # the flag sets before the ancestor recursion, so a cyclic
        #         hierarchy terminates with partial tables instead of recursing
        #         forever
        self.Inheritance_Compiled = True
        try:
            AN = str(self.Ancestor.Get_Input())
            if AN > '' and AN in Statement_Class.Names:
                S2 = Statement_Class.Names.get(AN)
                S2.Inherit()
                self.Compiled_Ancestors[AN] = S2
                N2 = ''
                Stmt = None
                for N2, Stmt in S2.Compiled_Ancestors.items():
                    self.Compiled_Ancestors[N2] = Stmt
                for N2, Stmt in S2.Compiled_Class_Properties.items():
                    self.Compiled_Class_Properties[N2] = Stmt
                for N2, Stmt in S2.Compiled_Class_Methods.items():
                    self.Compiled_Class_Methods[N2] = Stmt
                for N2, Stmt in S2.Compiled_Properties.items():
                    self.Compiled_Properties[N2] = Stmt
                for N2, Stmt in S2.Compiled_Methods.items():
                    self.Compiled_Methods[N2] = Stmt
                try:
                    if not (S2.Compiled_Constructor in (None, "")):
                        self.Compiled_Constructor = S2.Compiled_Constructor
                except Exception: pass
        except Exception: pass
        S = None
        try:
            for S in self.Block.Statements:
                try:
                    self.Inherit_Member(S)
                except Exception: pass
        except Exception: pass
        try:
            for S in self.Appended_Statements:
                try:
                    self.Inherit_Member(S)
                except Exception: pass
        except Exception: pass
        return 1
    def Infer_Attributes(self):
        Name = str(self.Class_Name.Get_Input())
        Statement_Class.Names[Name] = self
        return 1
    def Infer_Structure(self):
        try:
            self.Block.Parent = self
        except Exception:
            self.Block = Block()
            self.Block.Parent = self
        try:
            if self.Block.Dialect is None:
                raise ValueError
        except (ValueError, AttributeError):
            self.Block.Dialect = self.Dialect
        Elem = None
        for Elem in self.Arguments:
            try:
                if Elem.Dialect is None:
                    raise ValueError
            except (ValueError, AttributeError):
                Elem.Dialect = self.Dialect
            Elem.Parent = self
        Prev = None
        for Elem in self.Block.Statements:
            Elem.Parent = self
            try:
                if Elem.Dialect is None:
                    raise ValueError
            except (ValueError, AttributeError):
                Elem.Dialect = self.Dialect
            if Prev:
                # connect ifs to elses, etc. — on the
                #                 classifications, where Next_Else is consumed; the
                #                 element-level call stays for compatibility
                Prev.Next_Element(Elem)
                try:
                    Prev.Classification.Next_Element(Elem.Classification)
                except Exception: pass
            Prev = Elem
            if isinstance(Elem.Classification, Property_Statement):
                self.Generate_Constructor = True

class Derived_Class_Statement(Class_Statement):
    def Infer_Attributes(self):
        # a dialect, parser or symbol is class-like and registers
        #         under its name, but it must never displace a genuine class of the
        #         same name. the compiler stack declares both ’class Compiler’ and
        #         ’dialect Compiler’; the dialect is declared later, so it took the
        #         name - and ’class set Compiler’ then spliced its members into the
        #         dialect, where nothing emits them. they vanished from the atomic
        #         and from every artifact, silently. python tolerated the loss
        #         because the only caller is verbose-guarded; a static host does
        #         not
        Name = str(self.Name.Get_Input())
        if Name in Statement_Class.Names:
            Existing = Statement_Class.Names.get(Name)
            if not isinstance(Existing, Derived_Class_Statement):
                return 1
        Statement_Class.Names[Name] = self
        return 1

class Sideways_Class_Statement(Class_Statement):
    def Get_Language_Name(self):
        return self.Name.Get_Input()
    def Infer_Attributes(self):
        return 1

class Class_Append_Statement(Class_Statement):
    def __init__(self):
        super().__init__()
        self.Primary_Class = None # object
    def Infer_Appends(self):
        Status = 0
        Verbose = False
        Name = str(self.Class_Name.Get_Input())
        if Verbose:
            print(f'class set { Name }')
        if not Name in Statement_Class.Names:
            raise Exception(f"'class set' could not append to nonexistent class { Name }")
        C = Statement_Class.Names.get(Name)
        self.Primary_Class = C
        if self.End_Position > C.End_Position:
            C.End_Position = self.End_Position
        S = None
        for S in self.Block.Statements:
            if Verbose:
                print(f'class set to { Name }: { S.Classification.__class__.__name__ }')
            C.Appended_Statements.extend([S])
        return 1

class Language_Symbol_Statement(Scoped_Statement):
    pass
class Feature_Statement(Language_Symbol_Statement):
    pass
class Thing_Statement(Language_Symbol_Statement):
    pass
class Conditional_Statement(Scoped_Statement):
    pass
class If_Statement(Conditional_Statement):
    def __init__(self):
        super().__init__()
        self.Last_Else = None # object
        self.Next_Else = None # object
    def Next_Element(self, Next):
        # connect if to else.
        self.Next_Else = Next

class Else_If_Statement(If_Statement):
    def __init__(self):
        super().__init__()
        self.If_Statement = None # object

class Else_Statement(Conditional_Statement):
    def __init__(self):
        super().__init__()
        self.If_Statement = None # object

class Error_Handling_Statement(Scoped_Statement):
    pass
class Try_Statement(Error_Handling_Statement):
    def __init__(self):
        super().__init__()
        self.Last_Catch = None # object
        self.Next_Catch = None # object
    def Next_Element(self, Next):
        # connect try to catch.
        self.Next_Catch = Next

class Catch_Statement(Error_Handling_Statement):
    def __init__(self):
        super().__init__()
        self.Try_Statement = None # object

class Forgive_Statement(Error_Handling_Statement):
    pass
class Argument_Statement(Line_Statement):
    pass
class Module_Statement(Scoped_Statement):
    def __init__(self):
        super().__init__()
        self.Includes = [] # list
        self.Include_Set = {} # dictionary
        self.Variables = {} # dictionary
    def Get_Module(self):
        return self
    def Get_Variable_Context(self):
        return self
    def Lookup_Variable(self, Name):
        if Name in self.Variables:
            return self.Variables.get(Name)
        return ''
    def Add_Include(self, Code):
        if Code in self.Include_Set: return
        self.Includes.extend([Code])
        self.Include_Set[Code] = True

class Iteration_Statement(Scoped_Statement):
    pass
class For_Statement(Iteration_Statement):
    pass
class Dialect_Statement(Scoped_Statement):
    pass
class Class_Generator_Statement(Class_Statement):
    def Infer_Fallback(self):
        Base_Class = str(self.Base_Class)
        Class_Name = f'{ Base_Class }_{ self.Class_Name.Fallback }'
        Keyword = str(self.Verb_String.Fallback)
        Code = f'class { Class_Name } is '
        if self.Parent_Class is not None:
            Code += f'{ self.Parent_Class.Fallback }_'
        Code += Base_Class
        Code += f'\n{{\n    property string Keyword { Keyword };\n{ self.Block.Fallback_Statements }'
        Declarations = ''
        Dec = ''
        Stmt = None
        for Stmt in self.Block.Statements:
            Dec = Stmt.Classification.Fallback_Declaration
            if str(Stmt) == '':
                continue
            Declarations += f'{ Dec }\n'
        if Declarations > '':
            Declarations = self.Indent(Declarations)
        Attribute_Method = f'method number Attributes\n{{\n{ Declarations }    return 1;\n}}\n'
        Code += str(self.Indent(Attribute_Method))
        Code += '}\n'
        self.Fallback = Code

class Parse_Memo:
    def __init__(self):
        self.Success = False # flag
        self.Produced = [] # list
        self.End_Token = 0 # integer
        self.End_Char = 0 # integer
        self.In_Progress = False # flag
        self.Detected = False # flag
        self.Recorder = None # object
        self.Key = '' # string
        self.Start_Token = 0 # integer
    # one packrat memoization entry: the outcome of one rule at one
    #     token position. Produced holds the element objects the rule pushed, so a
    #     replay re-links the same objects and the element tree is identical to a
    #     fresh parse. In_Progress marks a seed planted for left-recursion support:
    #     a rule that reaches its own seed fails that attempt and sets Detected,
    #     which triggers seed-growing in the generated wrapper. Recorder collects
    #     the memo keys stored while the seed is live, so grow iterations can
    #     invalidate results that depended on the seed value.

class Parser:
    def __init__(self):
        self.Text = None # string
        self.Char_Pos = 0 # integer
        self.Token_Pos = 0 # integer
        self.Tokens = [] # list
        self.Elements = [] # list
        self.Memo = {} # dictionary
        self.Memo_Recorders = [] # list
        self.High_Water = 0 # integer
    def Top_Token(self):
        Verbose = False
        P = self.Token_Pos
        if P >= len(self.Tokens):
            if Verbose:
                print('top null')
            return None
        Top = self.Tokens[P]
        if Verbose:
            print(f'top token: { Top.To_String() }')
        return Top
    def Parse_Token(self, Elems, Expected):
        Verbose = False
        Top = self.Top_Token()
        if (Top in (None, "")): return False
        Text = str(Top.Text)
        if Text != Expected:
            if Verbose:
                print(f'parse_token expected <{ Expected }> but got <{ Text }>')
            return False
        if Verbose:
            print(f'parse_token found { Expected }')
        Elems.extend([self.Consume_Token()])
        return True
    def Rollback(self, CP, TP, Error):
        Verbose = False
        if Verbose:
            print(f'roll back to { CP }/{ TP }: { Error }')
        try:
            Top = self.Top_Token()
            Top.Error = Error
            if Verbose:
                print('recorded error')
        except Exception: pass
        self.Char_Pos = CP
        self.Token_Pos = TP
    def Consume_Token(self):
        Verbose = False
        if self.Token_Pos >= len(self.Tokens):
            if Verbose:
                print('cannot consume end token')
            return None
        Tok = self.Top_Token()
        (self.Token_Pos) += 1
        if self.Token_Pos > self.High_Water:
            # farthest consumption point: survives rollback, so a failed
            #             parse can still report where it actually got stuck
            self.High_Water = self.Token_Pos
        self.Char_Pos = Tok.End_Position + 1
        Tok.Error = None
        self.Elements.extend([Tok])
        if Verbose:
            print(f'consumed token { Tok.To_String() }')
        return Tok
    def Add_Element(self, Elem):
        self.Elements.extend([Elem])
    def Memo_Get(self, Key):
        if not Key in self.Memo: return None
        return self.Memo.get(Key)
    def Memo_Replay(self, Entry, Parent_Elements):
        # failure needs no position restore: rules roll back to their
        #         start position before returning false, and the key encodes that start.
        if Entry.In_Progress:
            # the rule reached its own seed: left recursion. fail this
            #             attempt so the base-case alternative can win, and start recording
            #             memo keys so grow iterations can invalidate dependent entries.
            #             the recorder stack holds the head entries themselves so settles
            #             can filter by position.
            Entry.Detected = True
            if (Entry.Recorder in (None, "")):
                R = []
                Entry.Recorder = R
                self.Memo_Recorders.extend([Entry])
            return False
        if not Entry.Success: return False
        self.Token_Pos = Entry.End_Token
        self.Char_Pos = Entry.End_Char
        Elem = None
        for Elem in Entry.Produced:
            Parent_Elements.extend([Elem])
        return True
    def Memo_Plant(self, Key):
        Entry = Parse_Memo()
        Entry.In_Progress = True
        Entry.Key = Key
        Entry.Start_Token = self.Token_Pos
        self.Memo[Key] = Entry
        return Entry
    def Memo_Settle(self, Entry, Result, Produced):
        Entry.In_Progress = False
        Entry.Success = Result
        Entry.Produced = Produced.copy()
        Entry.End_Token = self.Token_Pos
        Entry.End_Char = self.Char_Pos
        # record this outcome into live recorders at the same start
        #         position, excluding the head itself. positions only move forward in a
        #         parse, so an entry at a later position can never consult a seed at an
        #         earlier one: only same-position entries can depend on the seed, and
        #         restricting invalidation to them keeps grow iterations near-linear.
        Head = None
        for Head in self.Memo_Recorders:
            if Head == Entry:
                continue
            if Head.Start_Token != Entry.Start_Token:
                continue
            Head.Recorder.extend([Entry.Key])
    def Memo_Regrow_Begin(self, Entry):
        # invalidate the same-position entries recorded during the
        #         previous iteration: they may depend on the seed value that just
        #         changed. a null dictionary value reads as a miss in Memo_Get, so no
        #         delete is needed. the recorder stack holds the head entry itself, so
        #         replacing the recorder list needs no stack manipulation.
        K = ''
        for K in Entry.Recorder:
            self.Memo[K] = None
        R = []
        Entry.Recorder = R
    def Memo_Grew(self, Entry, Result, Produced):
        if not Result: return False
        if self.Token_Pos <= Entry.End_Token: return False
        Entry.Success = True
        Entry.Produced = Produced.copy()
        Entry.End_Token = self.Token_Pos
        Entry.End_Char = self.Char_Pos
        return True
    def Memo_Finish(self, Entry):
        if (Entry.Recorder in (None, "")): return
        Popped = self.Memo_Recorders.pop()
        Entry.Recorder = None

class Generator:
    def __init__(self, O=None):
        self.Status = False # flag
        self.Elements = [] # list
        self.Owner = None # object
        self.Owner = O

class Document(Element):
    def __init__(self):
        super().__init__()
        self.File_Name = None # string
        self.Text = None # string
    def Infer(self):
        self.Infer_Text()
        return 1
    def Infer_Text(self):
        Verbose = False
        if self.Text is not None: return 1.0
        FN = str(self.File_Name)
        if Verbose:
            print(f'infer text: { FN }')
        T = ''
        if os.path.exists(FN):
            with open(FN, 'r', encoding='utf-8') as _file:
                T = _file.read()
            self.Text = T
            if Verbose:
                print(f'success reading file { FN }')
            return 1
        else:
            raise Exception(f'no such file { FN }')
        return 0
    def Write_Text(self):
        with open(self.File_Name, 'w', encoding='utf-8') as _file:
            _file.write(self.Text)
        return 1

class Compiler(Document):
    def __init__(self):
        super().__init__()
        self.Parser = Parser() # object
        self.Generator = Generator(self) # object
        self.Dialect = None # object
        self.Characters = [] # list
        self.Tokens = [] # list
        self.Elements = [] # list
        self.Debug_Mode = True # flag
    def Initialize(self):
        if self.Dialect is not None:
            self.Dialect.Initialize()
    def Infer(self):
        Verbose = False
        Input_Result = self.Infer_Input()
        if Input_Result == 0:
            print('Infer_Input failed')
            return 0
        Output_Result = self.Infer_Output()
        if Output_Result == 0:
            print('Infer_Output failed')
            return 0
        # Printunclassifiedverbsfordebuggingpurposesif(defined [my Dialect])
        # 
        return 1
    def Infer_Input(self):
        Verbose = False
        if Verbose:
            print('Starting input inference pipeline...')
        Text_Result = self.Infer_Text()
        if Text_Result == 0:
            print('Failed at Infer_Text')
            return 0
        if Verbose:
            print('Infer_Text completed successfully')
        # Infer_Characters is no longer part of the standard pipeline:
        #         the string lexer in Scan_Tokens reads the text directly. lexers that
        #         still want per-character element objects (peg, pylex) call
        #         Infer_Characters themselves before their own Infer_Tokens.
        Tokens_Result = self.Infer_Tokens()
        if Tokens_Result == 0:
            print('Failed at Infer_Tokens')
            return 0
        if Verbose:
            print('Infer_Tokens completed successfully')
        Elements_Result = self.Infer_Elements()
        if Elements_Result == 0:
            print('Failed at Infer_Elements')
            return 0
        if Verbose:
            print('Infer_Elements completed successfully')
        # the element reports exist only for verbose tracing: build
        #         them only when verbosity is on, because each one renders the whole
        #         element list into text
        Report = ''
        Latest = ''
        if Verbose:
            Report = self.Element_Report()
            print(Report)
        Components_Result = self.Infer_Components()
        if Components_Result == 0:
            print('Failed at Infer_Components')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Components completed successfully')
        Classification_Result = self.Infer_Classification()
        if Classification_Result == 0:
            print('Failed at Infer_Classification')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Classification completed successfully')
        Attributes_Result = self.Infer_Attributes()
        if Attributes_Result == 0:
            print('Failed at Infer_Attributes')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Attributes completed successfully')
        Appends_Result = self.Infer_Appends()
        if Appends_Result == 0:
            print('Failed at Infer_Appends')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Appends completed successfully')
        Ordering_Result = self.Infer_Ordering()
        if Ordering_Result == 0:
            print('Failed at Infer_Ordering')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Ordering completed successfully')
        Structure_Result = self.Infer_Structure()
        if Structure_Result == 0:
            print('Failed at Infer_Structure')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Structure completed successfully')
        if Verbose:
            print('Input inference pipeline completed successfully')
        return 1
    def Infer_Output(self):
        Verbose = False
        if Verbose:
            print('Starting output inference pipeline...')
        Report = ''
        Latest = ''
        if Verbose:
            Report = self.Element_Report()
            print(Report)
        Variables_Result = self.Infer_Variables()
        if Variables_Result == 0:
            print('Failed at Infer_Variables')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Variables completed successfully')
        Type_Result = self.Infer_Type()
        if Type_Result == 0:
            print('Failed at Infer_Type')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Type completed successfully')
        Class_Structure_Result = self.Infer_Class_Structure()
        if Class_Structure_Result == 0:
            print('Failed at Infer_Class_Structure')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Class_Structure completed successfully')
        Inheritance_Result = self.Infer_Inheritance()
        if Inheritance_Result == 0:
            print('Failed at Infer_Inheritance')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Inheritance completed successfully')
        Code_Result = self.Infer_Code()
        if Code_Result == 0:
            print('Failed at Infer_Code')
            return 0
        if Verbose:
            Latest = self.Element_Report()
            if Latest != Report:
                print(Latest)
                Report = Latest
        if Verbose:
            print('Infer_Code completed successfully')
        # 
        #         number Intelligence_Result = (i Infer_Intelligence);
        #         if (Intelligence_Result = 0)
        #         {
        #             say ”Failed at Infer_Intelligence”;
        #             return 0;
        #         }
        #         
        if Verbose:
            print('Output inference pipeline completed successfully')
        return 1
    def Infer_Characters(self):
        if len(self.Characters) > 0: return 1.0
        Text = str(self.Text)
        Char = None
        C = ''
        N = None
        L = len(Text) - 1
        Prev = None
        for N in range(0,L+1):
            C = Text[N]
            Char = Character.Factory(self, N, C)
            if Prev is not None:
                Char.Prev = Prev
                Prev.Next = Char
            self.Characters.extend([Char])
            Prev = Char
        return 1
    def Infer_Tokens(self):
        return self.Scan_Tokens(True)
    def Token_Begin(self, Tok, C, P):
        Tok.Text = C
        Tok.Start_Position = P
        Tok.End_Position = P
    def Digit_At(self, P):
        T = str(self.Text)
        if P >= len(T):
            return False
        return T[P] in '0123456789'
    def Scan_Word_Tail(self, Tok, P):
        T = str(self.Text)
        L = len(T)
        C = ''
        while True:
            if P >= L:
                break
            C = T[P]
            Take = C in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789"
            if C in '0123456789':
                Take = True
            if not Take:
                break
            Tok.Text += C
            Tok.End_Position = P
            (P) += 1
        return P
    def Scan_Number_Tail(self, Tok, P):
        T = str(self.Text)
        L = len(T)
        C = ''
        while True:
            if P >= L:
                break
            C = T[P]
            if C in '0123456789':
                Tok.Text += C
                Tok.End_Position = P
                (P) += 1
            elif C == '.':
                # one decimal point, and only when a digit follows
                if '.' in Tok.Text:
                    break
                if not self.Digit_At(P + 1):
                    break
                Tok.Text += C
                Tok.End_Position = P
                (P) += 1
            else:
                break
        return P
    def Scan_Quote_Tail(self, Tok, P):
        T = str(self.Text)
        L = len(T)
        C = ''
        while True:
            if P >= L:
                break
            C = T[P]
            Tok.Text += C
            Tok.End_Position = P
            (P) += 1
            if C == str(Tok.Close_Quote):
                Tok.Open = False
                break
            Tok.Unquoted += C
        return P
    def Scan_Ws_Tail(self, Tok, P):
        T = str(self.Text)
        L = len(T)
        C = ''
        while True:
            if P >= L:
                break
            C = T[P]
            if C == str('\n'):
                break
            if not C in " \n\r\t":
                break
            Tok.Text += C
            Tok.End_Position = P
            (P) += 1
        return P
    def Scan_Tokens(self, Keep_Ws):
        # the string lexer: scans the source text directly by index,
        #         producing the same token stream (classes, text, positions, quote
        #         bookkeeping) the character-object pipeline produced, without one
        #         element per character. classification rules mirror Character:Factory
        #         composed with Token:Factory; the tail scanners mirror each token
        #         class’s Append_Character. when Keep_Ws is off, whitespace and line
        #         tokens are scanned but not kept, matching the gal compiler’s old
        #         Infer_Tokens override.
        Text = str(self.Text)
        L = len(Text)
        N = 0
        M = None
        C = ''
        Q = '"`“”‘’'
        Q += "'«»‹›"
        Tok = None
        Skip = None
        while True:
            if N >= L:
                break
            C = Text[N]
            M = N + 1
            Skip = False
            if C in Q:
                Tok = Token_Quote()
                Tok.Open_Quote = C
                Tok.Close_Quote = C
                if C == '“':
                    Tok.Close_Quote = '”'
                if C == '‘':
                    Tok.Close_Quote = '’'
                if C == '«':
                    Tok.Close_Quote = '»'
                if C == '‹':
                    Tok.Close_Quote = '›'
                self.Token_Begin(Tok, C, N)
                N = self.Scan_Quote_Tail(Tok, M)
            elif C in '0123456789':
                Tok = Token_Number()
                self.Token_Begin(Tok, C, N)
                N = self.Scan_Number_Tail(Tok, M)
            elif C in '-.' and self.Digit_At(M):
                Tok = Token_Number()
                self.Token_Begin(Tok, C, N)
                N = self.Scan_Number_Tail(Tok, M)
            elif C == ',':
                Tok = Token_Comma()
                self.Token_Begin(Tok, C, N)
                N = M
            elif C in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789":
                Tok = Token_Word()
                self.Token_Begin(Tok, C, N)
                N = self.Scan_Word_Tail(Tok, M)
            elif C == str('\n'):
                Tok = Token_Line()
                self.Token_Begin(Tok, C, N)
                N = M
                Skip = not Keep_Ws
            elif C in " \n\r\t":
                Tok = Token_Ws()
                self.Token_Begin(Tok, C, N)
                N = self.Scan_Ws_Tail(Tok, M)
                Skip = not Keep_Ws
            elif C in string.punctuation:
                if C in '{}[]();,':
                    Tok = Token_Boundary()
                    self.Token_Begin(Tok, C, N)
                    N = M
                elif C == '-':
                    Tok = Token_Word()
                    self.Token_Begin(Tok, C, N)
                    N = self.Scan_Word_Tail(Tok, M)
                else:
                    Tok = Token_Keyword()
                    self.Token_Begin(Tok, C, N)
                    N = M
            else:
                Msg = 'gal lexer: unclassifiable character <'
                Msg += f'{ C }> at position { str(N) }'
                raise Exception(Msg)
            if not Skip:
                self.Tokens.extend([Tok])
        return 1
    def Element_Report(self):
        return self.Elements[-1].To_String()
    def Infer_Elements(self):
        Elems = []
        P = self.Parser
        P.Text = self.Text
        P.Tokens = self.Tokens
        Status = P.Parse_Program(Elems)
        self.Elements = P.Elements
        self.Derive_Elements()
        return Status
    def Derive_Elements(self):
        # rebuild the flat element list as a post-order walk of the element
        #         tree, so dependency order (children before parents) is a property of the
        #         tree rather than of parse chronology. backtracking orphans and duplicate
        #         token consumptions vanish because they are unreachable from the root.
        if len(self.Elements) == 0: return 1
        Root = self.Elements[-1]
        Ordered = []
        self.Walk_Element(Root, Ordered)
        self.Elements = Ordered
        return 1
    def Walk_Element(self, Elem, Ordered):
        # post-order: children first, then self. stop at tokens, whose
        #         Elements hold the characters absorbed during lexing, not child elements.
        if isinstance(Elem, Token):
            Ordered.extend([Elem])
            return
        try:
            Child = None
            for Child in Elem.Elements:
                try:
                    if Child.Parent is None:
                        raise ValueError
                except (ValueError, AttributeError):
                    Child.Parent = Elem
                self.Walk_Element(Child, Ordered)
        except Exception: pass
        Ordered.extend([Elem])
    def Infer_Components(self):
        Verbose = False
        if Verbose:
            print(f'{ self.__class__.__name__ } infers components.')
        Elem = None
        for Elem in self.Elements:
            Elem.Infer_Components()
        return 1
    def Infer_Classification(self):
        Verbose = False
        if Verbose:
            print(f'{ self.__class__.__name__ } infers classification.')
        Elem = None
        End = len(self.Elements) - 1
        D = self.Dialect
        Index = None
        for Index in range(End,0+1,-1):
            Elem = self.Elements[Index]
            if isinstance(Elem, Spell):
                try:
                    Elem.Dialect.Classify(Elem)
                except Exception:
                    D.Classify(Elem)
        if Verbose:
            print(f'    { self.__class__.__name__ } components complete.')
        return 1
    def Infer_Appends(self):
        Verbose = False
        Elem = None
        Classification = None
        Status = 1
        This_Status = None
        for Elem in self.Elements:
            Classification = Elem.Classification
            if Verbose:
                print(f'inferring appends for { Classification.__class__.__name__ }')
            if Classification.Infer_Appends():
                continue
            print(f'FAILED inferring appends { Classification.__class__.__name__ }')
            Status = 0
        return Status
    def Infer_Ordering(self):
        Verbose = False
        # execute sideways inheritance: move the statement parse elements
        #         of each class set block into the primary class parse element, then
        #         re-derive the flat element list so appended members precede their class
        #         in dependency order. this makes single-pass bottom-up inference correct
        #         for classes extended by class set.
        Elem = None
        Class_Sets = []
        for Elem in self.Elements:
            try:
                if isinstance(Elem.Classification, Class_Append_Statement):
                    Class_Sets.extend([Elem])
            except Exception: pass
        if len(Class_Sets) == 0: return 1
        Spliced = False
        SE = None
        for SE in Class_Sets:
            try:
                if self.Splice_Class_Set(SE):
                    Spliced = True
            except Exception: pass
        if Spliced:
            self.Derive_Elements()
        return 1
    def Splice_Class_Set(self, SE):
        Verbose = False
        Target = SE.Classification.Primary_Class
        if (Target in (None, "")): return False
        CE = None
        Elem = None
        for Elem in self.Elements:
            if Elem.Classification == Target:
                CE = Elem
                break
        if (CE in (None, "")): return False
        SBlock = self.Get_Block_Element(SE)
        CBlock = self.Get_Block_Element(CE)
        if (SBlock in (None, "")): return False
        if (CBlock in (None, "")): return False
        if SBlock == CBlock: return False
        if Verbose:
            print(f'splicing class set into { Target.Class_Name.Get_Input() }')
        Kept = []
        Child = None
        Moved = False
        for Child in SBlock.Elements:
            if isinstance(Child, Statement):
                CBlock.Elements.extend([Child])
                Moved = True
            else:
                Kept.extend([Child])
        SBlock.Elements = Kept.copy()
        return Moved
    def Get_Block_Element(self, E):
        Found = None
        try:
            Child = None
            for Child in E.Elements:
                if isinstance(Child, Block):
                    Found = Child
        except Exception: pass
        return Found
    def Infer_Variables(self):
        Verbose = False
        # every declaration registers its name and type in the
        #         enclosing variable context, and every function registers its
        #         parameters; references then resolve through the context chain
        E = None
        for E in self.Elements:
            try:
                E.Classification.Register_Variables()
            except Exception: pass
        return 1
    def Infer_Type(self):
        Verbose = False
        Status = self.Infer_Data_Types()
        if Verbose:
            print(str(self.Data_Type_Report()))
        return Status
    def Infer_Class_Structure(self):
        # TODO: 
        return 1
    def Infer_Inheritance(self):
        # TODO: 
        return 1
    def Infer_Code(self):
        Verbose = False
        # Compiler elements are copied to the generator elements, and the generator is supposed to now Generate output code.
        if Verbose:
            print('Compiler infer code begin')
        self.Generator.Elements = self.Elements
        self.Generator.Generate()
        try:
            self.Gal = self.Generator.Gal
            if self.Debug_Mode:
                print('Successfully generated code')
            return 1
        except Exception as E:
            if self.Debug_Mode:
                print(f'Generator did not produce code: { E }')
            raise Exception('generator does not have gal code, fix gal inference.')
        if Verbose:
            print('Compiler infer code end')
    def Infer_Intelligence(self):
        Prog = self.Elements[-1]
        return Prog.Infer_Intelligence()
    def Error_Report(self):
        Text = 'ERROR REPORT\n'
        Elem = None
        Count = 0
        for Elem in self.Elements:
            try:
                if Elem.Error is None:
                    raise ValueError
            except (ValueError, AttributeError):
                continue
            if (Elem.Error in (None, "")):
                continue
            Text += f'{ str(Count) }. { Elem.__class__.__name__ }'
            Text += f' ERROR <{ str(Elem.Error) }>'
            Text += str('\n')
            # append Text (substring (Elem.Get_Input) 0 80);
            #             append Text [line 2];
            (Count) += 1
        return Text
    def Data_Type_Report(self):
        # coverage over the current program: how many elements
        #         carry each definitional type and each usage, and which
        #         classification classes remain untyped - the same
        #         coverage-driven shape as the unclassified verbs report
        Types = {}
        Usages = {}
        Untyped = {}
        Count = None
        E = None
        for E in self.Elements:
            C = E.Classification
            if (C in (None, "")):
                continue
            DT = ''
            U = ''
            try:
                DT = C.Data_Type
            except Exception: pass
            try:
                U = C.Usage
            except Exception: pass
            # some classifications bind Data_Type and Usage to
            #             declaration elements rather than strings; those are not
            #             inferred types and do not belong in the counts
            if isinstance(DT, Element):
                DT = ''
            if isinstance(U, Element):
                U = ''
            if DT > '':
                # dget yields null for a missing key rather than
                #                 raising, so the count must be guarded by dexists - a
                #                 forgive around it never fires and leaves Count null
                Count = 0
                if DT in Types:
                    Count = Types.get(DT)
                Types[DT] = Count + 1
            elif isinstance(C, Operation):
                CN = str(C.__class__.__name__)
                Count = 0
                if CN in Untyped:
                    Count = Untyped.get(CN)
                Untyped[CN] = Count + 1
            if U > '':
                Count = 0
                if U in Usages:
                    Count = Usages.get(U)
                Usages[U] = Count + 1
        Text = 'DATA TYPE REPORT\n'
        K = ''
        V = None
        Text += 'definitional:\n'
        for K, V in Types.items():
            Text += f'  { K } { str(V) }\n'
        Text += 'usage:\n'
        for K, V in Usages.items():
            Text += f'  { K } { str(V) }\n'
        Text += 'untyped operations:\n'
        for K, V in Untyped.items():
            Text += f'  { K } { str(V) }\n'
        return Text
    def Infer_Attributes(self):
        Verbose = True
        E = None
        for E in self.Elements:
            try:
                E.Classification.Attributes()
                E.Classification.Infer_Attributes()
            except Exception as Err:
                import pdebug; pdebug.zbreak()
                C = E.Classification
                if not C:
                    C = E
                Class_Name = str(C.__class__.__name__)
                print(f'Error: { Err }, inferring { Class_Name } attributes, position { E.Start_Position }-{ E.End_Position }')
                if Verbose:
                    print(f'    input: { E.Get_Input() }\n{ E.Classification.To_String() }')
                if Verbose:
                    print(str('\n'))
        # an explicit success: python’s fall-off None passed the
        #         caller’s = 0 check only by accident, and a static host cannot
        #         return None
        return 1
    def Infer_Structure(self):
        Verbose = False
        if Verbose:
            print(f'{ self.__class__.__name__ } begins inferring structure')
        Elem = None
        CurrentElem = None
        Status = True
        # Printthelanguageelementsforanalysis
        if Verbose:
            print('Analyzing elements for structure inference...')
        ElementCount = len(self.Elements)
        if Verbose:
            print(f'Found { ElementCount } elements to process')
        # First pass: establish direct parent-child relationships
        # Working from right to left (end to beginning) to ensure all
        # component elements are processed before their owners
        N = None
        L = ElementCount - 1
        if Verbose:
            print(f'Processing elements in reverse order (index { L } to 0)')
        for N in range(L,0+1,-1):
            CurrentElem = self.Elements[N]
            try:
                if CurrentElem.Dialect is None:
                    raise ValueError
            except (ValueError, AttributeError):
                CurrentElem.Dialect = self.Dialect
            CurrentElem.Infer_Structure()
            try:
                CurrentElem.Classification.Parent = CurrentElem.Parent.Classification
            except Exception: pass
            CurrentElem.Classification.Infer_Structure()
        if Verbose:
            print(f'{ self.__class__.__name__ } completed inferring structure')
        return Status
    def Infer_Data_Types(self):
        Verbose = False
        E = None
        for E in self.Elements:
            try:
                E.Classification.Infer_Data_Types()
            except Exception as Err:
                C = E.Classification
                if not C:
                    C = E
                print(f'Error inferring data types for { C.__class__.__name__ }: { Err }')
                return 0
        return 1
    def Infer_Inheritance(self):
        Verbose = False
        E = None
        C = None
        for E in self.Elements:
            try:
                C = E.Classification
                if isinstance(C, Class_Statement):
                    C.Inherit()
            except Exception: pass
        return 1

class Inference(Symbol):
    def Get(self):
        return self.Symbol_Value
    def Assign(self, Val):
        self.Symbol_Value = Val
    def Exists(self):
        try:
            if self.Symbol_Value is not None: return True
        except Exception: pass
        return False
    def Default(self, Val):
        if self.Symbol_Value is not None: return self.Symbol_Value
        return Val
    def Compute(self):
        raise Exception(f'{ self.__class__ } did not override the Compute method')

# ******************************************************************************
# * the compiler dialect, language elements necessary for the compiler to run. *
# ******************************************************************************
class Statement_Flowerbox(Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'flower box' # string
    def Attributes(self):
        return 1
    def Infer_Data_Types(self):
        self.Argument_Types('string')
        return 1
    def Infer_Gal(self):
        Code = f'flower box{ self.Gal_Arguments() }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Comment_Text = ''
        Argument = None
        for Argument in self.Arguments:
            Arg_Text = str(Argument.Fallback)
            if isinstance(Argument, Token_Quote):
                Arg_Text = Argument.Unquoted
            Comment_Text += Arg_Text
        Lines = Comment_Text.split('\n')
        Comment_Text = ''
        Line = ""
        Full = ""
        Width = 0
        for Line in Lines:
            if len(Line) > Width:
                Width = len(Line)
        for Line in Lines:
            Full = f'{ Line }                                                                                                          '
            Full = Full[0:(0)+(Width)]
            Full = f'* { Full } *'
            Comment_Text += f' { self.Enquote(Full) } [line]'
        Width += 4
        Stars = f'''"{ '****************************************************************************************************************'[0:(0)+(Width)] }"'''
        Comment_Text = f'{ Stars } [line] { Comment_Text } { Stars }'
        Code = f'comment { Comment_Text };'
        self.Fallback = Code

class Statement_Colon(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = ':' # string
        self.Class_Name = None # object
        self.Method_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Method_Name')
        self.Method_Name = self.Listargs.pop(0)
        self.Method_Name.Value = 'method'
        self.Method_Name.Usage = 'method'
        return 1
    def Infer_Gal(self):
        Code = f'{ self.Class_Name.Gal }:{ self.Method_Name.Gal }{ self.Gal_Args() };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'{ self.Class_Name.Fallback }:{ self.Method_Name.Fallback }{ self.Fallback_Args() };'
        self.Fallback = Code

class Statement_Argument(Argument_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'argument' # string
        self.Argument_Name = None # object
        self.Data_Type = None # object
        self.Usage = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Argument_Name')
        self.Argument_Name = self.Listargs.pop(0)
        self.Argument_Name.Value = 'property'
        self.Argument_Name.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Data_Type')
        self.Data_Type = self.Listargs.pop(0)
        self.Data_Type.Value = 'type'
        self.Data_Type.Usage = 'string'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Usage')
        self.Usage = self.Listargs.pop(0)
        self.Usage.Value = 'usage'
        self.Usage.Usage = 'string'
        return 1
    def Infer_Gal(self):
        Code = f'argument { self.Argument_Name.Gal } { self.Data_Type.Gal } { self.Usage.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Argument_Name = str(self.Argument_Name.Fallback)
        Code = f'property object { Argument_Name };'
        Declaration = f"if ((llength [my Listargs]) = 0)\n{{\n    error 'missing required argument { Argument_Name }';\n}}\nmy { Argument_Name } = (shift [my Listargs]);\n"
        Declaration += f'[my { Argument_Name } Value] = { self.Data_Type.Fallback };\n'
        Declaration += f'[my { Argument_Name } Usage] = { self.Usage.Fallback };\n'
        self.Fallback_Declaration = Declaration
        self.Fallback = Code

class Statement_Optional(Argument_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'optional' # string
        self.Argument_Name = None # object
        self.Data_Type = None # object
        self.Usage = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Argument_Name')
        self.Argument_Name = self.Listargs.pop(0)
        self.Argument_Name.Value = 'property'
        self.Argument_Name.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Data_Type')
        self.Data_Type = self.Listargs.pop(0)
        self.Data_Type.Value = 'type'
        self.Data_Type.Usage = 'string'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Usage')
        self.Usage = self.Listargs.pop(0)
        self.Usage.Value = 'usage'
        self.Usage.Usage = 'string'
        return 1
    def Infer_Fallback(self):
        Argument_Name = str(self.Argument_Name.Fallback)
        Code = f'property object { Argument_Name };'
        Declaration = f'if ((llength [my Listargs]) > 0)\n{{\n    my { Argument_Name } = (shift [my Listargs]);\n    [my { Argument_Name } Value] = { self.Data_Type.Fallback };\n    [my { Argument_Name } Usage] = { self.Usage.Fallback };\n}}\n'
        self.Fallback_Declaration = Declaration
        self.Fallback = Code

class Statement_Statement(Class_Generator_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'statement' # string
        self.Class_Name = None # object
        self.Verb_String = None # object
        self.Parent_Class = None # object
        self.Base_Class = 'Statement' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Verb_String')
        self.Verb_String = self.Listargs.pop(0)
        self.Verb_String.Value = 'string'
        self.Verb_String.Usage = 'string'
        if len(self.Listargs) > 0:
            self.Parent_Class = self.Listargs.pop(0)
            self.Parent_Class.Value = 'class'
            self.Parent_Class.Usage = 'class'
        return 1
    def Infer_Attributes(self):
        Name = f'Statement_{ self.Class_Name.Get_Input() }'
        Statement_Class.Names[Name] = self
        return 1

class Statement_Operation(Class_Generator_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'operation' # string
        self.Class_Name = None # object
        self.Verb_String = None # object
        self.Parent_Class = None # object
        self.Base_Class = 'Operation' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Verb_String')
        self.Verb_String = self.Listargs.pop(0)
        self.Verb_String.Value = 'string'
        self.Verb_String.Usage = 'string'
        if len(self.Listargs) > 0:
            self.Parent_Class = self.Listargs.pop(0)
            self.Parent_Class.Value = 'class'
            self.Parent_Class.Usage = 'class'
        return 1
    def Infer_Attributes(self):
        Name = f'Operation_{ self.Class_Name.Get_Input() }'
        Statement_Class.Names[Name] = self
        return 1

class Statement_Syntax(Class_Generator_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'syntax' # string
        self.Class_Name = None # object
        self.Verb_String = None # object
        self.Parent_Class = None # object
        self.Base_Class = 'Syntax' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Verb_String')
        self.Verb_String = self.Listargs.pop(0)
        self.Verb_String.Value = 'string'
        self.Verb_String.Usage = 'string'
        if len(self.Listargs) > 0:
            self.Parent_Class = self.Listargs.pop(0)
            self.Parent_Class.Value = 'class'
            self.Parent_Class.Usage = 'class'
        return 1
    def Infer_Attributes(self):
        Name = f'Syntax_{ self.Class_Name.Get_Input() }'
        Statement_Class.Names[Name] = self
        return 1

class Statement_Class(Class_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'class' # string
        self.Class_Name = None # object
        self.Ancestor = None # object
    Names = {} # class property dictionary
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        if len(self.Listargs) > 0:
            self.Ancestor = self.Listargs.pop(0)
            self.Ancestor.Value = 'class'
            self.Ancestor.Usage = 'class'
        return 1
    def Infer_Gal(self):
        Class_Name = str(self.Class_Name.Gal)
        Ancestor = ''
        try:
            if self.Ancestor is None:
                raise ValueError
            if isinstance(self.Ancestor, Syntax_Is):
                Ancestor += f' { self.Ancestor.Gal }'
            else:
                Ancestor += f' is { self.Ancestor.Gal }'
        except (ValueError, AttributeError):
            pass
        Block = str(self.Gal_Block())
        Code = f'class { Class_Name }{ Ancestor }{ Block }'
        self.Gal = Code
    def Infer_Fallback(self):
        Class_Name = str(self.Class_Name.Fallback)
        Ancestor = ''
        try:
            if self.Ancestor is None:
                raise ValueError
            if isinstance(self.Ancestor, Syntax_Is):
                Ancestor += f' { self.Ancestor.Fallback }'
            else:
                Ancestor += f' is { self.Ancestor.Fallback }'
        except (ValueError, AttributeError):
            pass
        Block = str(self.Fallback_Block())
        Append_Stmts = ''
        Stmt = None
        for Stmt in self.Appended_Statements:
            try:
                Append_Stmts += f'{ Stmt.Fallback }\n'
            except Exception:
                Append_Stmts += f'{ Stmt.Gal }\n'
        if Block != ';':
            Block_Stmts = str(self.Block.Fallback_Statements)
            Append_Stmts = self.Indent(Append_Stmts)
            Block = f'\n{{\n{ Block_Stmts }{ Append_Stmts }}}'
        elif Append_Stmts > '':
            Append_Stmts = self.Indent(Append_Stmts)
            Block = f'\n{{\n{ Append_Stmts }}}'
        Code = f'class { Class_Name }{ Ancestor }{ Block }'
        self.Fallback = Code

class Statement_Class_Set(Class_Append_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'class set' # string
        self.Class_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        return 1
    def Infer_Attributes(self):
        return 1
    def Infer_Gal(self):
        Code = f'class set { self.Class_Name.Gal }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Verbose = False
        Code = ''
        if not self.Primary_Class is not None:
            Code += f'class set { self.Fallback_Arguments() }{ self.Fallback_Block() }'
        if Verbose:
            print(f'fallback class set: { Code }')
        self.Fallback = Code

class Statement_Class_Method(Method_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'class method' # string
        self.Data_Type = None # object
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Data_Type')
        self.Data_Type = self.Listargs.pop(0)
        self.Data_Type.Value = 'type'
        self.Data_Type.Usage = 'string'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'method'
        self.Name.Usage = 'method'
        return 1
    def Infer_Gal(self):
        Code = f'class method{ self.Gal_Arguments() }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'class method{ self.Fallback_Arguments() }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_Keyword(Argument_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'keyword' # string
        self.Argument_Name = None # object
        self.Data_Type = None # object
        self.Usage = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Argument_Name')
        self.Argument_Name = self.Listargs.pop(0)
        self.Argument_Name.Value = 'property'
        self.Argument_Name.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Data_Type')
        self.Data_Type = self.Listargs.pop(0)
        self.Data_Type.Value = 'type'
        self.Data_Type.Usage = 'string'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Usage')
        self.Usage = self.Listargs.pop(0)
        self.Usage.Value = 'usage'
        self.Usage.Usage = 'string'
        return 1
    def Infer_Fallback(self):
        Argument_Name = str(self.Argument_Name.Fallback)
        Code = f'property object { Argument_Name };'
        Declaration = f"if ((llength [my Listargs]) = 0)\n{{\n    error 'missing required keyword { Argument_Name }';\n}}\nmy { Argument_Name } = (shift [my Listargs]);\n"
        Declaration += f'    [my { Argument_Name } Usage] = { self.Usage.Fallback };\n'
        Declaration += f'    [my { Argument_Name } Value] = { self.Data_Type.Fallback };\n'
        self.Fallback_Declaration = Declaration
        self.Fallback = Code

class Statement_Method(Method_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'method' # string
        self.Data_Type = None # object
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required keyword Data_Type')
        self.Data_Type = self.Listargs.pop(0)
        self.Data_Type.Usage = 'string'
        self.Data_Type.Value = 'type'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'method'
        self.Name.Usage = 'method'
        return 1
    def Infer_Gal(self):
        Code = f'method{ self.Gal_Arguments() }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'method{ self.Fallback_Arguments() }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_Property(Property_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'property' # string
        self.Type = None # object
        self.Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required keyword Type')
        self.Type = self.Listargs.pop(0)
        self.Type.Usage = 'string'
        self.Type.Value = 'type'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'property'
        self.Name.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'value'
            self.Value.Usage = 'variant'
        return 1
    def Infer_Gal(self):
        Type = str(self.Type.Gal)
        Name = str(self.Name.Gal)
        Code = f'property { Type } { Name }'
        try:
            if self.Value is None:
                raise ValueError
            Code += f' = { self.Value.Gal }'
        except (ValueError, AttributeError):
            pass
        Code += ';'
        self.Gal = Code
    def Infer_Fallback(self):
        Type = str(self.Type.Fallback)
        Name = str(self.Name.Fallback)
        Code = f'property { Type } { Name }'
        try:
            if self.Value is None:
                raise ValueError
            Code += f' = { self.Value.Fallback }'
        except (ValueError, AttributeError):
            pass
        Code += ';'
        self.Fallback = Code

class Statement_Class_Property(Property_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'class property' # string
        self.Type = None # object
        self.Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required keyword Type')
        self.Type = self.Listargs.pop(0)
        self.Type.Usage = 'string'
        self.Type.Value = 'type'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'property'
        self.Name.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'value'
            self.Value.Usage = 'variant'
        return 1
    def Infer_Gal(self):
        Type = str(self.Type.Gal)
        Name = str(self.Name.Gal)
        Code = f'class property { Type } { Name }'
        try:
            if self.Value is None:
                raise ValueError
            Code += f' = { self.Value.Gal }'
        except (ValueError, AttributeError):
            pass
        Code += ';'
        self.Gal = Code
    def Infer_Fallback(self):
        Type = str(self.Type.Fallback)
        Name = str(self.Name.Fallback)
        Code = f'class property { Type } { Name }'
        try:
            if self.Value is None:
                raise ValueError
            Code += f' = { self.Value.Fallback }'
        except (ValueError, AttributeError):
            pass
        Code += ';'
        self.Fallback = Code

class Statement_Flag(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'flag' # string
        self.Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'flag'
            self.Value.Usage = 'value'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('flag')
        return 1

class Statement_Integer(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'integer' # string
        self.Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'integer'
            self.Value.Usage = 'value'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('integer')
        return 1

class Statement_Number(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'number' # string
        self.Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'number'
            self.Value.Usage = 'value'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('number')
        return 1

class Statement_String(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'string' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('string')
        return 1
    def Infer_Gal(self):
        Code = f'string{ self.Gal_Arguments() };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'string{ self.Fallback_Arguments() };'
        self.Fallback = Code

class Statement_I_Equal(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'i =' # string
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value')
        self.Value = self.Listargs.pop(0)
        self.Value.Value = 'string'
        self.Value.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Property_Name = ''
        try:
            Property_Name = self.Get_Property_Name()
        except Exception:
            import pdebug; pdebug.zbreak()
        if (Property_Name in (None, "")):
            try:
                Property_Name = self.Get_Language_Name()
            except Exception:
                import pdebug; pdebug.zbreak()
        if (Property_Name in (None, "")):
            import pdebug; pdebug.zbreak()
        Code = f'my { Property_Name } = { self.Value.Fallback };'
        self.Fallback = Code

class Statement_Object(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'object' # string
        self.Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'object'
            self.Value.Usage = 'value'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('object')
        return 1

class Statement_Dictionary(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'dict' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('dictionary')
        return 1
    def Infer_Gal(self):
        Code = f'dictionary { self.Name.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'dictionary { self.Name.Fallback };'
        self.Fallback = Code

class Statement_List(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'list' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('list')
        return 1
    def Infer_Gal(self):
        Code = f'list{ self.Gal_Arguments() };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'list{ self.Fallback_Arguments() };'
        self.Fallback = Code

class Statement_Global_List(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'global list' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('list')
        return 1

class Statement_Variant(Declaration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'variant' # string
        self.Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'variant'
            self.Value.Usage = 'value'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        self.Declare_Name_Type('variant')
        return 1

class Statement_Module(Module_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'module' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        return 1
    def Infer_Data_Types(self):
        try:
            N = self.Name
            NC = N.Classification
            NC.Data_Type = 'module'
            NC.Usage = 'module'
        except Exception: pass
        return 1

class Statement_If(If_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'if' # string
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Condition')
        self.Condition = self.Listargs.pop(0)
        self.Condition.Value = 'flag'
        self.Condition.Usage = 'value'
        return 1

class Statement_Else_If(Else_If_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'else if' # string
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Condition')
        self.Condition = self.Listargs.pop(0)
        self.Condition.Value = 'flag'
        self.Condition.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'else if{ self.Gal_Arguments() }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'else if{ self.Fallback_Arguments() }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_Else(Else_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'else' # string
    def Attributes(self):
        return 1
    def Infer_Gal(self):
        Code = f'else{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'else{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_Forever(For_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'forever' # string
    def Attributes(self):
        return 1

class Statement_Try(Try_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'try' # string
    def Attributes(self):
        return 1

class Statement_Catch(Catch_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'catch' # string
        self.Error = None # object
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Error = self.Listargs.pop(0)
            self.Error.Value = 'variable'
            self.Error.Usage = 'variable'
        return 1
    def Infer_Gal(self):
        Code = f'catch{ self.Gal_Arguments() }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'catch{ self.Fallback_Arguments() }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_For_Range(For_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'for range' # string
        self.Variable = None # object
        self.Start = None # object
        self.End = None # object
        self.Increment = None # object
    def Register_Variables(self):
        # the loop variable of a counted range is definitionally an
        #         integer: references inside the loop body then resolve their type,
        #         which the strongly typed targets need to format it
        try:
            Ctx = self.Get_Variable_Context()
            if (Ctx in (None, "")): return
            N = self.Variable
            Ctx.Variables[N.Get_Input()] = 'integer'
        except Exception: pass
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'number'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Start')
        self.Start = self.Listargs.pop(0)
        self.Start.Value = 'number'
        self.Start.Usage = 'number'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument End')
        self.End = self.Listargs.pop(0)
        self.End.Value = 'number'
        self.End.Usage = 'number'
        if len(self.Listargs) > 0:
            self.Increment = self.Listargs.pop(0)
            self.Increment.Value = 'number'
            self.Increment.Usage = 'number'
        return 1

class Statement_For_Each_In(For_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'for each in' # string
        self.Item = None # object
        self.List = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Item')
        self.Item = self.Listargs.pop(0)
        self.Item.Value = 'variant'
        self.Item.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'list'
        return 1
    def Infer_Gal(self):
        Code = f'for each { self.Item.Gal } in { self.List.Gal }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'for each { self.Item.Fallback } in { self.List.Fallback }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_For_Each(For_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'foreach' # string
        self.List = None # object
        self.Item = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'list'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Item')
        self.Item = self.Listargs.pop(0)
        self.Item.Value = 'variant'
        self.Item.Usage = 'variable'
        return 1

class Statement_Iterate(Iteration_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'iterate' # string
        self.Dictionary = None # object
        self.Key_Variable = None # object
        self.Value_Variable = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Dictionary')
        self.Dictionary = self.Listargs.pop(0)
        self.Dictionary.Value = 'dict'
        self.Dictionary.Usage = 'dict'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Key_Variable')
        self.Key_Variable = self.Listargs.pop(0)
        self.Key_Variable.Value = 'variable'
        self.Key_Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value_Variable')
        self.Value_Variable = self.Listargs.pop(0)
        self.Value_Variable.Value = 'variable'
        self.Value_Variable.Usage = 'variable'
        return 1

class Statement_Return(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'return' # string
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'flag'
            self.Value.Usage = 'value'
        return 1

class Statement_Inference(Sideways_Class_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'inference' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'variable'
        self.Name.Usage = 'variable'
        return 1
    def Infer_Fallback(self):
        Code = f'comment "inference { self.Name.Fallback }";\n'
        Stmt = None
        try:
            for Statement in self.Block.Statements:
                Code += f'{ Statement.Fallback }\n'
        except Exception: pass
        Code += f'\ncomment "END inference { self.Name.Fallback }";\n'
        self.Fallback = Code

class Statement_Handle(Sideways_Method_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'handle' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'class'
        self.Name.Usage = 'class'
        return 1
    def Infer_Fallback(self):
        Class_Name = str(self.Name.Fallback)
        Inference = str(self.Parent.Get_Language_Name())
        Method = f'method flag Infer_{ Inference }{ self.Fallback_Block() }'
        Code = f'class set { Class_Name }\n{{\n{ self.Indent(Method) }\n}}'
        self.Fallback = Code

class Statement_Defined(Conditional_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'defined' # string
        self.Expression = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Expression')
        self.Expression = self.Listargs.pop(0)
        self.Expression.Value = 'variable'
        self.Expression.Usage = 'variable'
        return 1
    def Infer_Gal(self):
        Code = f'defined { self.Expression.Gal }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'defined { self.Expression.Fallback }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_Undefined(Conditional_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'undefined' # string
        self.Expression = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Expression')
        self.Expression = self.Listargs.pop(0)
        self.Expression.Value = 'variable'
        self.Expression.Usage = 'variable'
        return 1
    def Infer_Gal(self):
        Code = f'undefined { self.Expression.Gal }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'undefined { self.Expression.Fallback }{ self.Fallback_Block() }'
        self.Fallback = Code

class Statement_Dialect(Derived_Class_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'dialect' # string
        self.Name = None # object
        self.Ancestor = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'class'
        self.Name.Usage = 'class'
        if len(self.Listargs) > 0:
            self.Ancestor = self.Listargs.pop(0)
            self.Ancestor.Value = 'class'
            self.Ancestor.Usage = 'class'
        return 1
    def Infer_Gal(self):
        Code = f'dialect{ self.Gal_Arguments() }{ self.Gal_Block() }'
        self.Gal = Code
    def Infer_Fallback(self):
        Name = str(self.Name.Fallback)
        Ancestor = 'Dialect'
        if self.Ancestor is not None:
            Ancestor = f'{ self.Ancestor.Fallback }_Dialect'
        Body = ''
        Fback = f'my Name = { self.Enquote(Name) };\n'
        Statement = None
        if self.Block is not None:
            for Statement in self.Block.Statements:
                if isinstance(Statement, (Method_Statement, Statement_Main)):
                    Body += f'{ Statement.Fallback }\n'
                else:
                    if Statement.Fallback_Declaration is not None:
                        Body += f'{ Statement.Fallback_Declaration }\n'
                    if Statement.Fallback is not None:
                        Fback += f'{ Statement.Fallback }\n'
        Method = f'method flag Initialize\n{{\n    object Element;\n{ self.Indent(Fback) }\n    return [true];\n}}'
        Body = self.Indent(Body)
        Method = self.Indent(Method)
        Code = f'class Dialect_{ Name } is { Ancestor }\n{{\n{ self.Indent(Method) }{ self.Indent(Body) }}}\n'
        self.Fallback = Code

class Statement_Parser(Derived_Class_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'parser' # string
        self.Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'class'
        self.Name.Usage = 'class'
        return 1
    def Infer_Fallback(self):
        Verbose = False
        Declarations = ''
        Statement = None
        try:
            for Statement in self.Block.Statements:
                try:
                    if Statement.Fallback_Declaration is None:
                        raise ValueError
                    Declarations += str(Statement.Fallback_Declaration)
                except (ValueError, AttributeError):
                    pass
        except Exception: pass
        Args = str(self.Fallback_Args())
        Block = str(self.Fallback_Block())
        Code = f'class { self.Name.Fallback }_Parser is Parser{ Args }{ Block }{ Declarations }'
        self.Fallback_Declaration = Declarations
        self.Fallback = Code

class Statement_Append(Append_Args_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'append' # string
        self.Variable = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'variable'
        self.Variable.Usage = 'variable'
        return 1
    def Infer_Data_Types(self):
        self.Declared_Usage()
        Arg = None
        try:
            for Arg in self.Listargs:
                AC2 = Arg.Classification
                if str(AC2.Usage) == '':
                    AC2.Usage = 'string'
        except Exception: pass
        return 1
    def Infer_Gal(self):
        Code = f'append{ self.Gal_Arguments() };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'append{ self.Fallback_Arguments() };'
        self.Fallback = Code

class Statement_Push(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'push' # string
        self.List = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'variable'
        return 1

class Operation_Not_Equal(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '!=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } != { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } ne { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Add(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '+' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 6 # integer
        self.Javascript_Precedence = 6 # integer
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } + { self.Op2.Gal }{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } + { self.Op2.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_And(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'and' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 13 # integer
        self.Javascript_Precedence = 13 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'flag'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'flag'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } and { self.Op2.Gal }{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } and { self.Op2.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Call(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '.' # string
        self.Object = None # object
        self.Method = None # object
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Object')
        self.Object = self.Listargs.pop(0)
        self.Object.Value = 'object'
        self.Object.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Method')
        self.Method = self.Listargs.pop(0)
        self.Method.Value = 'method'
        self.Method.Usage = 'variable'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Object.Gal }.{ self.Method.Gal }{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Object.Fallback }.{ self.Method.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Colon(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = ':' # string
        self.Class = None # object
        self.Method = None # object
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class')
        self.Class = self.Listargs.pop(0)
        self.Class.Value = 'class'
        self.Class.Usage = 'class'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Method')
        self.Method = self.Listargs.pop(0)
        self.Method.Value = 'method'
        self.Method.Usage = 'method'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Class.Gal }:{ self.Method.Gal }{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Class.Fallback }:{ self.Method.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Append(Append_Args_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'append' # string
        self.Variable = None # object
        self.Python_Precedence = 6 # integer
        self.Javascript_Precedence = 6 # integer
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'variable'
        self.Variable.Usage = 'variable'
        return 1
    def Infer_Data_Types(self):
        Arg = None
        try:
            for Arg in self.Arguments:
                AC3 = Arg.Classification
                if str(AC3.Usage) == '':
                    AC3.Usage = 'string'
        except Exception: pass
        return 1
    def Infer_Gal(self):
        Code = f'(append{ self.Gal_Arguments() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'(append{ self.Fallback_Arguments() })'
        self.Fallback = Code

class Operation_Contains(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'contains' # string
        self.String = None # object
        self.Search = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument String')
        self.String = self.Listargs.pop(0)
        self.String.Value = 'string'
        self.String.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Search')
        self.Search = self.Listargs.pop(0)
        self.Search.Value = 'string'
        self.Search.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.String.Gal } contains { self.Search.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.String.Fallback } contains { self.Search.Fallback })'
        self.Fallback = Code

class Operation_Defined(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'defined' # string
        self.Variable = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'variable'
        self.Variable.Usage = 'variable'
        return 1

class Operation_Dict_Exists(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'dict exists' # string
        self.Dictionary = None # object
        self.Key = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Dictionary')
        self.Dictionary = self.Listargs.pop(0)
        self.Dictionary.Value = 'variable'
        self.Dictionary.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Key')
        self.Key = self.Listargs.pop(0)
        self.Key.Value = 'string'
        self.Key.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Dictionary.Gal } dexists { self.Key.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Dictionary.Fallback } dexists { self.Key.Fallback })'
        self.Fallback = Code

class Operation_Dict_Get(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'dict get' # string
        self.Dictionary = None # object
        self.Key = None # object
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Dictionary')
        self.Dictionary = self.Listargs.pop(0)
        self.Dictionary.Value = 'variable'
        self.Dictionary.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Key')
        self.Key = self.Listargs.pop(0)
        self.Key.Value = 'string'
        self.Key.Usage = 'value'
        return 1

class Operation_Divide(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '/' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 5 # integer
        self.Javascript_Precedence = 5 # integer
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } / { self.Op2.Gal }{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } / { self.Op2.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Modulo(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'mod' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 5 # integer
        self.Javascript_Precedence = 5 # integer
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } mod { self.Op2.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Minus(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '-' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 6 # integer
        self.Javascript_Precedence = 6 # integer
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Op2 = self.Listargs.pop(0)
            self.Op2.Value = 'variant'
            self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = ''
        if len(self.Arguments):
            Code += f'({ self.Op1.Gal } - { self.Op2.Gal }{ self.Gal_Args() })'
        else:
            Code += f'(-{ self.Gal_Arguments() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = ''
        if len(self.Arguments):
            Code += f'({ self.Op1.Fallback } - { self.Op2.Fallback }{ self.Fallback_Args() })'
        else:
            Code += f'(-{ self.Fallback_Arguments() })'
        self.Fallback = Code

class Operation_Multiply(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '*' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 5 # integer
        self.Javascript_Precedence = 5 # integer
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } * { self.Op2.Gal }{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } * { self.Op2.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Equal(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } = { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } eq { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_File_Exists(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'file exists' # string
        self.Path = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Path')
        self.Path = self.Listargs.pop(0)
        self.Path.Value = 'string'
        self.Path.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'(file { self.Path.Gal } exists)'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'(file { self.Path.Fallback } exists)'
        self.Fallback = Code

class Operation_Greater(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '>' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } > { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } gt { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Less(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '<' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } < { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } lt { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Greater_Equal(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '>=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } >= { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } ge { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Less_Equal(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = '<=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } <= { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } le { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_I(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'i' # string
        self.Method = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Method')
        self.Method = self.Listargs.pop(0)
        self.Method.Value = 'method'
        self.Method.Usage = 'method'
        return 1
    def Infer_Fallback(self):
        Code = f'(i { self.Method.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Is_A(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is a' # string
        self.Object = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Object')
        self.Object = self.Listargs.pop(0)
        self.Object.Value = 'object'
        self.Object.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Object.Gal } is a{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Object.Fallback } is a{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Is_Alpha(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is alpha' # string
        self.Character = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Character')
        self.Character = self.Listargs.pop(0)
        self.Character.Value = 'string'
        self.Character.Usage = 'value'
        return 1

class Operation_Is_Ident(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is ident' # string
        self.Character = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Character')
        self.Character = self.Listargs.pop(0)
        self.Character.Value = 'string'
        self.Character.Usage = 'value'
        return 1

class Operation_Is_Lower(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is lowercase' # string
        self.First = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument First')
        self.First = self.Listargs.pop(0)
        self.First.Value = 'string'
        self.First.Usage = 'value'
        return 1

class Operation_Is_Upper(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is uppercase' # string
        self.First = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument First')
        self.First = self.Listargs.pop(0)
        self.First.Value = 'string'
        self.First.Usage = 'value'
        return 1

class Operation_Is_Whitespace(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is whitespace' # string
        self.Character = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Character')
        self.Character = self.Listargs.pop(0)
        self.Character.Value = 'string'
        self.Character.Usage = 'value'
        return 1

class Operation_Is_Numeric(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is numeric' # string
        self.Character = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Character')
        self.Character = self.Listargs.pop(0)
        self.Character.Value = 'string'
        self.Character.Usage = 'value'
        return 1

class Operation_Is_Punctuation(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is punctuation' # string
        self.Character = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Character')
        self.Character = self.Listargs.pop(0)
        self.Character.Value = 'string'
        self.Character.Usage = 'value'
        return 1

class Operation_Is_Null(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is null' # string
        self.Op1 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } is null)'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } is null)'
        self.Fallback = Code

class Operation_Length(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'length' # string
        self.First = None # object
        self.Python_Precedence = 1 # integer
        self.Javascript_Precedence = 1 # integer
        self.Data_Type = 'integer' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument First')
        self.First = self.Listargs.pop(0)
        self.First.Value = 'string'
        self.First.Usage = 'value'
        return 1

class Operation_List_Get(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'lget' # string
        self.List = None # object
        self.Offset = None # object
        self.Python_Precedence = 1 # integer
        self.Javascript_Precedence = 1 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Offset')
        self.Offset = self.Listargs.pop(0)
        self.Offset.Value = 'integer'
        self.Offset.Usage = 'value'
        return 1

class Operation_List_Last(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'llast' # string
        self.List = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'value'
        return 1

class Operation_List_Length(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'llength' # string
        self.List = None # object
        self.Data_Type = 'integer' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'(llength { self.List.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'(llength { self.List.Fallback })'
        self.Fallback = Code

class Operation_New(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'new' # string
        self.Class_Name = None # object
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
        self.Data_Type = 'object' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        return 1
    def Infer_Data_Types(self):
        self.Data_Type = 'object'
        try:
            C = self.Class_Name
            CC = C.Classification
            CC.Data_Type = 'class'
            CC.Usage = 'class'
        except Exception: pass
        return 1

class Operation_Not(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'not' # string
        self.Op1 = None # object
        self.Python_Precedence = 12 # integer
        self.Javascript_Precedence = 3 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'flag'
        self.Op1.Usage = 'value'
        return 1

class Operation_Not_Null(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'not null' # string
        self.Op1 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'string'
        self.Op1.Usage = 'value'
        return 1

class Operation_Or(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'or' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 14 # integer
        self.Javascript_Precedence = 14 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'flag'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'flag'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } or { self.Op2.Gal }{ self.Gal_Args() })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } or { self.Op2.Fallback }{ self.Fallback_Args() })'
        self.Fallback = Code

class Operation_Pop(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'pop' # string
        self.List = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'value'
        return 1

class Operation_Shift(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'shift' # string
        self.List = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'value'
        return 1

class Operation_Split(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'split' # string
        self.String = None # object
        self.Delimiter = None # object
        self.Data_Type = 'list' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument String')
        self.String = self.Listargs.pop(0)
        self.String.Value = 'string'
        self.String.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Delimiter')
        self.Delimiter = self.Listargs.pop(0)
        self.Delimiter.Value = 'string'
        self.Delimiter.Usage = 'value'
        return 1

class Operation_String_Equal(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 's=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } s= { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } seq { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_String_Greater(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 's>' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } sgt { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } sgt { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_String_Greater_Equal(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 's>=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } sge { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } sge { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_String_Less(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 's<' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } slt { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } slt { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_String_Less_Equal(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 's<=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } sle { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } sle { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_String_Not_Equal(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 's!=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'({ self.Op1.Gal } sne { self.Op2.Gal })'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } sne { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Substring(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'substring' # string
        self.String_Value = None # object
        self.Start_Index = None # object
        self.Length = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument String_Value')
        self.String_Value = self.Listargs.pop(0)
        self.String_Value.Value = 'string'
        self.String_Value.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Start_Index')
        self.Start_Index = self.Listargs.pop(0)
        self.Start_Index.Value = 'integer'
        self.Start_Index.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Length = self.Listargs.pop(0)
            self.Length.Value = 'integer'
            self.Length.Usage = 'value'
        return 1

class Operation_Is_Not_A(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is not a' # string
        self.Object = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Object')
        self.Object = self.Listargs.pop(0)
        self.Object.Value = 'object'
        self.Object.Usage = 'value'
        return 1

class Syntax_Class(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'class' # string
        self.Object = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Object')
        self.Object = self.Listargs.pop(0)
        self.Object.Value = 'object'
        self.Object.Usage = 'value'
        return 1

class Syntax_Class_Name(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'class name' # string
        self.Object = None # object
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Object = self.Listargs.pop(0)
            self.Object.Value = 'object'
            self.Object.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Target = ''
        try:
            Target = self.Object.Gal
            Target += ' '
        except Exception: pass
        Code = f'[{ Target }class name]'
        self.Gal = Code
    def Infer_Fallback(self):
        Target = ''
        try:
            Target = self.Object.Fallback
            Target += ' '
        except Exception: pass
        Code = f'[{ Target }class name]'
        self.Fallback = Code

class Syntax_Colon(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = ':' # string
        self.Class_Name = None # object
        self.Property_Name = None # object
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Property_Name')
        self.Property_Name = self.Listargs.pop(0)
        self.Property_Name.Value = 'property'
        self.Property_Name.Usage = 'property'
        return 1

class Syntax_Dictionary(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'dictionary' # string
        self.Variable = None # object
        self.Data_Type = 'dictionary' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'dictionary'
        self.Variable.Usage = 'variable'
        return 1

class Syntax_False(Literal_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'false' # string
        self.Data_Type = 'flag' # string
    def Attributes(self):
        return 1

class Syntax_Flag(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'flag' # string
        self.Variable = None # object
        self.Default_Value = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'flag'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Default_Value = self.Listargs.pop(0)
            self.Default_Value.Value = 'flag'
            self.Default_Value.Usage = 'value'
        return 1

class Syntax_Indent(Literal_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'indent' # string
        self.Count = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Count = self.Listargs.pop(0)
            self.Count.Value = 'integer'
            self.Count.Usage = 'value'
        return 1

class Syntax_Integer(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'integer' # string
        self.Variable = None # object
        self.Default_Value = None # object
        self.Data_Type = 'integer' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'integer'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) > 0:
            self.Default_Value = self.Listargs.pop(0)
            self.Default_Value.Value = 'integer'
            self.Default_Value.Usage = 'value'
        return 1

class Syntax_Line(Literal_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'line' # string
        self.Count = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Count = self.Listargs.pop(0)
            self.Count.Value = 'integer'
            self.Count.Usage = 'value'
        return 1

class Syntax_List(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'list' # string
        self.Variable = None # object
        self.Data_Type = 'list' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'list'
        self.Variable.Usage = 'variable'
        return 1

class Syntax_My(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'my' # string
        self.Property = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Property')
        self.Property = self.Listargs.pop(0)
        self.Property.Value = 'property'
        self.Property.Usage = 'property'
        return 1
    def Infer_Data_Types(self):
        # a simple my reference takes the type of the property it
        #         names on the owner class; chained references stay untyped for now
        if str(self.Data_Type) == '':
            try:
                if len(self.Listargs) == 0:
                    Cls = self.Get_Owner_Class()
                    if (Cls in (None, "")): return 1
                    P = self.Property
                    N = str(P.Get_Input())
                    if N in Cls.Variables:
                        self.Data_Type = Cls.Variables.get(N)
            except Exception: pass
        return 1
    def Infer_Gal(self):
        Code = f'[my { self.Property.Gal }{ self.Gal_Args() }]'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'[my { self.Property.Fallback }{ self.Fallback_Args() }]'
        self.Fallback = Code

class Syntax_My_Class(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'my class' # string
    def Attributes(self):
        return 1

class Syntax_Null(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'null' # string
    def Attributes(self):
        return 1

class Syntax_Number(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'number' # string
        self.Variable = None # object
        self.Default_Value = None # object
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'number'
        self.Variable.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Default_Value = self.Listargs.pop(0)
            self.Default_Value.Value = 'number'
            self.Default_Value.Usage = 'value'
        return 1

class Syntax_Object(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'object' # string
        self.Variable = None # object
        self.Default_Value = None # object
        self.Data_Type = 'object' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'object'
        self.Variable.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Default_Value = self.Listargs.pop(0)
            self.Default_Value.Value = 'object'
            self.Default_Value.Usage = 'value'
        return 1

class Syntax_Our(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'our' # string
        self.Class_Property = None # object
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Class_Property = self.Listargs.pop(0)
            self.Class_Property.Value = 'property'
            self.Class_Property.Usage = 'property'
        return 1

class Syntax_Property(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = '.' # string
        self.Object = None # object
        self.Property_Name = None # object
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Object')
        self.Object = self.Listargs.pop(0)
        self.Object.Value = 'object'
        self.Object.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Property_Name')
        self.Property_Name = self.Listargs.pop(0)
        self.Property_Name.Value = 'property'
        self.Property_Name.Usage = 'property'
        return 1
    def Infer_Gal(self):
        Code = f'[{ self.Object.Gal }.{ self.Property_Name.Gal }{ self.Gal_Args() }]'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'[{ self.Object.Fallback }.{ self.Property_Name.Fallback }{ self.Fallback_Args() }]'
        self.Fallback = Code

class Syntax_Return(Literal_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'return' # string
        self.Count = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Count = self.Listargs.pop(0)
            self.Count.Value = 'integer'
            self.Count.Usage = 'value'
        return 1

class Syntax_Self(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'self' # string
    def Attributes(self):
        return 1

class Syntax_String(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'string' # string
        self.Variable = None # object
        self.Default_Value = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'string'
        self.Variable.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Default_Value = self.Listargs.pop(0)
            self.Default_Value.Value = 'string'
            self.Default_Value.Usage = 'value'
        return 1

class Syntax_Tab(Literal_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'tab' # string
        self.Count = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Count = self.Listargs.pop(0)
            self.Count.Value = 'integer'
            self.Count.Usage = 'value'
        return 1

class Syntax_True(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'true' # string
        self.Data_Type = 'flag' # string
    def Attributes(self):
        return 1

class Syntax_Us(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'us' # string
    def Attributes(self):
        return 1

class Syntax_Variant(Argument_Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'variant' # string
        self.Variable = None # object
        self.Default_Value = None # object
        self.Data_Type = 'variant' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'variant'
        self.Variable.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Default_Value = self.Listargs.pop(0)
            self.Default_Value.Value = 'variant'
            self.Default_Value.Usage = 'value'
        return 1

class Statement_Say(Append_Args_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'say' # string
    def Attributes(self):
        return 1
    def Infer_Data_Types(self):
        self.Argument_Types('string')
        return 1

class Statement_Readline(Append_Args_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'readline' # string
    def Attributes(self):
        return 1

class Statement_Main(Method_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'main' # string
    def Attributes(self):
        return 1

class Statement_Verbosity(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'verbosity' # string
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) > 0:
            self.Condition = self.Listargs.pop(0)
            self.Condition.Value = 'flag'
            self.Condition.Usage = 'flag'
        return 1
    def Infer_Fallback(self):
        Condition = '[false]'
        try:
            if self.Condition is None:
                raise ValueError
            Condition = self.Condition.Fallback
        except (ValueError, AttributeError):
            pass
        Code = f'flag Verbose { Condition };'
        self.Fallback = Code

class Statement_Verbose(Append_Args_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'verbose' # string
    def Attributes(self):
        return 1
    def Infer_Data_Types(self):
        self.Argument_Types('string')
        return 1
    def Infer_Fallback(self):
        Code = f'if Verbose\n{{\n    say{ self.Fallback_Arguments() };\n}}'
        self.Fallback = Code

class Statement_Call(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = '.' # string
        self.Object = None # object
        self.Method = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Object')
        self.Object = self.Listargs.pop(0)
        self.Object.Value = 'object'
        self.Object.Usage = 'object'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Method')
        self.Method = self.Listargs.pop(0)
        self.Method.Value = 'method'
        self.Method.Usage = 'method'
        return 1
    def Infer_Gal(self):
        Code = f'{ self.Object.Gal }.{ self.Method.Gal }{ self.Gal_Args() };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'{ self.Object.Fallback }.{ self.Method.Fallback }{ self.Fallback_Args() };'
        self.Fallback = Code

class Statement_Propset(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = '. =' # string
        self.Object = None # object
        self.Property = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Object')
        self.Object = self.Listargs.pop(0)
        self.Object.Value = 'object'
        self.Object.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Property')
        self.Property = self.Listargs.pop(0)
        self.Property.Value = 'property'
        self.Property.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value')
        self.Value = self.Listargs.pop(0)
        self.Value.Value = 'variant'
        self.Value.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'{ self.Object.Gal }.{ self.Property.Gal } = { self.Value.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'{ self.Object.Fallback }.{ self.Property.Fallback } = { self.Value.Fallback };'
        self.Fallback = Code

class Statement_Write_To(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'write to' # string
        self.Text = None # object
        self.File = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Text')
        self.Text = self.Listargs.pop(0)
        self.Text.Value = 'string'
        self.Text.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument File')
        self.File = self.Listargs.pop(0)
        self.File.Value = 'string'
        self.File.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'write { self.Text.Gal } to file { self.File.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'write { self.Text.Fallback } to file { self.File.Fallback };'
        self.Fallback = Code

class Statement_List_Split(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'list split' # string
        self.Variable = None # object
        self.String = None # object
        self.Delimiter = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'list'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument String')
        self.String = self.Listargs.pop(0)
        self.String.Value = 'string'
        self.String.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Delimiter')
        self.Delimiter = self.Listargs.pop(0)
        self.Delimiter.Value = 'string'
        self.Delimiter.Usage = 'value'
        return 1

class Statement_List_Copy(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'list copy' # string
        self.Target = None # object
        self.Source = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Target')
        self.Target = self.Listargs.pop(0)
        self.Target.Value = 'list'
        self.Target.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Source')
        self.Source = self.Listargs.pop(0)
        self.Source.Value = 'list'
        self.Source.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'list { self.Target.Gal } copy of { self.Source.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'list { self.Target.Fallback } copy of { self.Source.Fallback };'
        self.Fallback = Code

class Statement_I(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'i' # string
        self.Method = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Method')
        self.Method = self.Listargs.pop(0)
        self.Method.Value = 'method'
        self.Method.Usage = 'method'
        return 1
    def Infer_Gal(self):
        Code = f'i{ self.Gal_Arguments() };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'i{ self.Fallback_Arguments() };'
        self.Fallback = Code

class Statement_Constructor(Scoped_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'constructor' # string
    def Attributes(self):
        return 1

class Statement_Super(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'super' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        # validated once here, then passed through to the atomic
        #         unchanged: super may only appear inside a constructor of a class
        #         that declares an ancestor. backends render it without re-checking;
        #         each constructor generator separately requires it to be the first
        #         statement
        Ctor = self.Get_Owner_Constructor()
        if (Ctor in (None, "")):
            raise Exception('super must appear inside a constructor')
        Cls = self.Get_Owner_Class()
        Has_Ancestor = ''
        try:
            # the dereference throws when Ancestor is unset (missing
            #             attribute or null), under gal2- and gal3-built binaries alike
            Probe = str(Cls.Ancestor.Get_Input())
            Has_Ancestor = 'y'
        except Exception: pass
        if Has_Ancestor == '':
            raise Exception('super requires the class to declare an ancestor')
        Code = f'super{ self.Fallback_Args() };'
        self.Fallback = Code

class Statement_Forgive(Scoped_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'forgive' # string
    def Attributes(self):
        return 1

class Statement_Return_If(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'return if' # string
        self.Value = None # object
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value')
        self.Value = self.Listargs.pop(0)
        self.Value.Value = 'variant'
        self.Value.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Condition = self.Listargs.pop(0)
            self.Condition.Value = 'flag'
            self.Condition.Usage = 'value'
        return 1
    def Infer_Attributes(self):
        try:
            if self.Condition is None:
                raise ValueError
        except (ValueError, AttributeError):
            self.Condition = self.Value
            self.Value = None
    def Infer_Gal(self):
        Condition = str(self.Condition.Gal)
        Code = 'return '
        if self.Value:
            Code += f'{ self.Value.Gal } '
        Code += f'if { Condition };'
        self.Gal = Code
    def Infer_Fallback(self):
        Condition = str(self.Condition.Fallback)
        Code = 'return '
        if self.Value:
            Code += f'{ self.Value.Fallback } '
        Code += f'if { Condition };'
        self.Fallback = Code

class Statement_If_Return(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'if return' # string
        self.Condition = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Condition')
        self.Condition = self.Listargs.pop(0)
        self.Condition.Value = 'flag'
        self.Condition.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Value = self.Listargs.pop(0)
            self.Value.Value = 'variant'
            self.Value.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Condition = str(self.Condition.Gal)
        Code = f'if { Condition } return'
        if self.Value is not None:
            Value = str(self.Value.Gal)
            Code += f' { Value }'
        Code += ';'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'if { self.Condition.Fallback } return'
        try:
            if self.Value is None:
                raise ValueError
            Code += f' { self.Value.Fallback }'
        except (ValueError, AttributeError):
            pass
        Code += ';'
        self.Fallback = Code

class Statement_Assign(Scoped_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = '=' # string
        self.Destination = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Destination')
        self.Destination = self.Listargs.pop(0)
        self.Destination.Value = 'variable'
        self.Destination.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value')
        self.Value = self.Listargs.pop(0)
        self.Value.Value = 'variant'
        self.Value.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'{ self.Destination.Gal } = { self.Value.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'{ self.Destination.Fallback } = { self.Value.Fallback };'
        self.Fallback = Code

class Statement_Todo(Comment_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'todo' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        Code = f'comment "TODO: "{ self.Fallback_Arguments() };'
        self.Fallback = Code

class Statement_My_Equal(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'my =' # string
        self.Property_Name = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Property_Name')
        self.Property_Name = self.Listargs.pop(0)
        self.Property_Name.Value = 'property'
        self.Property_Name.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value')
        self.Value = self.Listargs.pop(0)
        self.Value.Value = 'variant'
        self.Value.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'my { self.Property_Name.Gal } = { self.Value.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'my { self.Property_Name.Fallback } = { self.Value.Fallback };'
        self.Fallback = Code

class Statement_Add(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = '+=' # string
        self.Destination = None # object
        self.Increment = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Destination')
        self.Destination = self.Listargs.pop(0)
        self.Destination.Value = 'number'
        self.Destination.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Increment')
        self.Increment = self.Listargs.pop(0)
        self.Increment.Value = 'number'
        self.Increment.Usage = 'value'
        return 1

class Statement_Continue(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'continue' # string
    def Attributes(self):
        return 1

class Statement_Continue_If(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'continue if' # string
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Condition')
        self.Condition = self.Listargs.pop(0)
        self.Condition.Value = 'flag'
        self.Condition.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'if{ self.Fallback_Arguments() } {{ continue; }}'
        self.Fallback = Code

class Statement_Debug(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'debug' # string
    def Attributes(self):
        return 1

class Statement_Debug_If(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'debug if' # string
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Condition')
        self.Condition = self.Listargs.pop(0)
        self.Condition.Value = 'flag'
        self.Condition.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'if { self.Condition.Fallback } {{ debug; }}'
        self.Fallback = Code

class Statement_Decrement(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = '--' # string
        self.Destination = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Destination')
        self.Destination = self.Listargs.pop(0)
        self.Destination.Value = 'integer'
        self.Destination.Usage = 'variable'
        return 1

class Statement_Increment(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = '++' # string
        self.Destination = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Destination')
        self.Destination = self.Listargs.pop(0)
        self.Destination.Value = 'integer'
        self.Destination.Usage = 'variable'
        return 1

class Statement_Error(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'error' # string
    def Attributes(self):
        return 1
    def Infer_Data_Types(self):
        self.Argument_Types('string')
        return 1

class Statement_Comment(Comment_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = '#' # string
    def Attributes(self):
        return 1
    def Infer_Data_Types(self):
        self.Argument_Types('string')
        return 1

class Statement_File_Read(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'fread' # string
        self.Variable = None # object
        self.File_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'string'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument File_Name')
        self.File_Name = self.Listargs.pop(0)
        self.File_Name.Value = 'string'
        self.File_Name.Usage = 'value'
        return 1

class Statement_Include(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'include' # string
        self.Name = None # object
    # splice the contents of a compiled plugin file into the source
    #     in place of this statement. the argument is a bare plugin name; the
    #     ’.gal’ suffix is imposed. an included file is the output of a previous
    #     gal-stage compilation, whose own include statements were resolved when
    #     it was built, so includes can never recurse. resolution happens in the
    #     gal stage only (see the Gal generator); a .gal file must never contain
    #     an include statement.
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'string'
        self.Name.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Name = ''
        try:
            Name = self.Name.Unquoted
        except Exception: pass
        if Name == '':
            raise Exception('include requires a quoted plugin name')
        FN = f'{ Name }.gal'
        if not os.path.exists(FN):
            raise Exception(f'include: no such file { FN }')
        T = ''
        with open(FN, 'r', encoding='utf-8') as _file:
            T = _file.read()
        self.Gal = T
    def Infer_Fallback(self):
        raise Exception('include statement in fallback input; includes are resolved by the gal stage (compile the .txt source with gal first)')

class Statement_Shell_Capture(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'shell capture' # string
        self.Variable = None # object
        self.Command = None # object
    # run a shell command and capture the result into a dictionary
    #     with stdout, stderr and exit_code keys. the command runs through a real
    #     shell, so pipes, redirection and quoting work.
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'dictionary'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Command')
        self.Command = self.Listargs.pop(0)
        self.Command.Value = 'string'
        self.Command.Usage = 'value'
        return 1

class Statement_Dictionary_Assign(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'd=' # string
        self.Dict = None # object
        self.Subscript = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Dict')
        self.Dict = self.Listargs.pop(0)
        self.Dict.Value = 'ditionary'
        self.Dict.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Subscript')
        self.Subscript = self.Listargs.pop(0)
        self.Subscript.Value = 'variant'
        self.Subscript.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value')
        self.Value = self.Listargs.pop(0)
        self.Value.Value = 'variant'
        self.Value.Usage = 'value'
        return 1
    def Infer_Gal(self):
        Code = f'{ self.Dict.Gal } { self.Subscript.Gal } d= { self.Value.Gal };'
        self.Gal = Code
    def Infer_Fallback(self):
        Code = f'{ self.Dict.Fallback } { self.Subscript.Fallback } d= { self.Value.Fallback };'
        self.Fallback = Code

class Syntax_Is(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'is' # string
        self.Class_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        return 1

class Statement_Join(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'join' # string
        self.Variable = None # object
        self.List = None # object
        self.Delimiter = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'string'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Delimiter')
        self.Delimiter = self.Listargs.pop(0)
        self.Delimiter.Value = 'string'
        self.Delimiter.Usage = 'value'
        return 1

class Statement_Either(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'either' # string
        self.Rule_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Rule_Name')
        self.Rule_Name = self.Listargs.pop(0)
        self.Rule_Name.Value = 'method'
        self.Rule_Name.Usage = 'method'
        return 1
    def Infer_Fallback(self):
        Verbose = False
        Rule_Name = str(self.Rule_Name.Fallback)
        Declarations = ''
        Quoted_Input = str(self.Enquote(self.Get_Input()))
        Block = f'comment { Quoted_Input };\n'
        if Verbose:
            Block += f'verbosity [true];\nverbose "Parse " { Quoted_Input };\n'
        Argument = None
        for Argument in self.Listargs:
            if Verbose:
                Block += f"verbose [indent] { self.Enquote(f'Either { Rule_Name } trying { Argument.Get_Input() }') };\n"
            try:
                if Argument.Fallback_Declaration is None:
                    raise ValueError
                Declarations += str(Argument.Fallback_Declaration)
            except (ValueError, AttributeError):
                pass
            if isinstance(Argument, (Token_Quote, Syntax_Line, Syntax_Tab)):
                Block += f'return [true] if (i Parse_Token Parent_Elements { Argument.Fallback });\n'
            elif isinstance(Argument, Token):
                Block += f'return [true] if (i Parse_{ Argument.Fallback } Parent_Elements);\n'
            else:
                Block += str(Argument.Fallback)
        if Verbose:
            Block += f'verbose "FAILED " { Quoted_Input };\n'
        Block = self.Indent(Block)
        Wrapper = str(self.Indent(self.Fallback_Memo_Wrapper(Rule_Name)))
        Code = f'method flag Parse_{ Rule_Name } [list Parent_Elements]\n{{\n{ Wrapper }}}\nmethod flag Parse_{ Rule_Name }_Rule [list Parent_Elements]\n{{\n{ Block }    return [false];\n}}'
        self.Fallback_Declaration = Declarations
        self.Fallback = Code

class Statement_English(Comment_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'english' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        Code = f'comment "ENGLISH: "{ self.Fallback_Arguments() };'
        self.Fallback = Code

class Statement_Entity(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'entity' # string
    def Attributes(self):
        return 1

class Statement_Flags(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'flags' # string
    def Attributes(self):
        return 1

class Statement_Integers(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'integers' # string
    def Attributes(self):
        return 1

class Statement_Numbers(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'numbers' # string
    def Attributes(self):
        return 1

class Statement_Strings(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'strings' # string
    def Attributes(self):
        return 1

class Statement_Lists(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'lists' # string
    def Attributes(self):
        return 1

class Statement_Dictionaries(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'dictionaries' # string
    def Attributes(self):
        return 1

class Statement_Objects(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'objects' # string
    def Attributes(self):
        return 1

class Statement_Variants(Declarations_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'variants' # string
    def Attributes(self):
        return 1

class Statement_Generate(Sideways_Method_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'generate' # string
        self.Class_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        return 1
    def Infer_Fallback(self):
        Language = str(self.Parent.Get_Language_Name())
        Class_Name = str(self.Class_Name.Fallback)
        Argument = None
        Method_Prefix = ''
        Method_Suffix = ''
        if len(self.Listargs) > 0:
            Method_Prefix += '    string Code'
            for Argument in self.Listargs:
                if isinstance(Argument.Classification, Token_Word):
                    Method_Prefix += f' [my { Argument.Fallback } { Language }]'
                else:
                    Method_Prefix += f' { Argument.Fallback }'
            Method_Prefix += ';\n'
            Method_Suffix += f'    my { Language } = Code;\n'
        Method_Statements = f'{ Method_Prefix }{ self.Fallback_Statements() }{ Method_Suffix }'
        Method_Code = f'method flag Infer_{ Language }\n{{\n{ Method_Statements }}}'
        Code = f'class set { Class_Name }\n{{\n{ self.Indent(Method_Code) }\n}}'
        self.Fallback = Code

class Statement_Generator(Scoped_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'generator' # string
        self.Language = None # object
        self.Ancestor = None # object
    def Get_Language_Name(self):
        return self.Language.Get_Input()
    def Get_Property_Name(self):
        return self.Language.Get_Input()
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Language')
        self.Language = self.Listargs.pop(0)
        self.Language.Value = 'class'
        self.Language.Usage = 'class'
        if len(self.Listargs) > 0:
            self.Ancestor = self.Listargs.pop(0)
            self.Ancestor.Value = 'class'
            self.Ancestor.Usage = 'class'
        return 1
    def Infer_Fallback(self):
        Language = str(self.Language.Fallback)
        Ancestor = 'Generator'
        try:
            if self.Ancestor is None:
                raise ValueError
            Ancestor = f'{ self.Ancestor.Fallback }_Generator'
        except (ValueError, AttributeError):
            pass
        Fallback_Statements = ''
        Fallback_Declaration = ''
        Statement = None
        for Statement in self.Block.Statements:
            Statement_Fb = str(Statement.Fallback)
            Statement_Dec = str(Statement.Fallback_Declaration)
            if Statement_Dec > '':
                Fallback_Declaration += f'{ Statement_Dec }\n'
            if Statement_Fb > '':
                Fallback_Statements += f'{ Statement_Fb }\n'
        Class = f'{ Language }_Generator'
        Class_Definition = f'''class { Class } is { Ancestor }\n{{\n    property flag Verbosity [false];\n    property string Language_Name { self.Enquote(Language) };\n    property string Property_Name { self.Enquote(Language) };\n    constructor [object Owner [null]]\n    {{\n        my Owner = Owner;\n    }}\n    method flag Infer_{ Language }\n    {{\n        comment "this verbosity defined in gal3 fallback_inference.txt for Statement_Generator.";\n        verbosity [my Verbosity];\n        object Elem;\n        object I;\n        integer Number = -1;\n        variant Error;\n        my Status = [true];\n        for each Elem in [my Elements]\n        {{\n            try\n            {{\n                Number++;\n                if (defined [Elem.Classification])\n                {{\n                    I = [Elem.Classification];\n                    I.Infer_{ Language };\n                    Elem.{ Language } = [I.{ Language }];\n                }}\n                else\n                {{\n                    Elem.Infer_{ Language };\n                }}\n            }}\n            catch Error\n            {{\n                my Status = [false];\n                Elem.Error = Error;\n                verbose '!error! { Language } element ' Number ': ' [class name I] ', <' Error '>';\n            }}\n        }}\n        return [false] if (not [my Status]);\n        object Top = (llast [my Elements]);\n        Top.Infer_{ Language };\n        string Code [Top.{ Language }];\n        my { Language } = Code;\n        my Code = Code;\n        return [true];\n    }}\n}}\n'''
        Code = f'{ Fallback_Declaration }{ Class_Definition }{ Fallback_Statements }'
        self.Fallback = Code

class Statement_Operations(Dialect_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'operations' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        Arg = None
        Tail = None
        Operation = 'ERROR_UNKNOWN_OPERATION'
        Keyword = 'ERROR_UNKNOWN_KEYWORD'
        Code = ''
        for Tail in self.Arguments:
            for Arg in Tail.Elements:
                if isinstance(Arg, Token_Comma):
                    Operation = 'ERROR_UNKNOWN_STATEMENT'
                    Keyword = 'ERROR_UNKNOWN_KEYWORD'
                    continue
                if isinstance(Arg, Token_Quote):
                    Keyword = Arg.Fallback
                    Code += f'[my Operations] { Keyword } d= Element;\ni Add_Keywords { Keyword };\n'
                elif isinstance(Arg, Token_Word):
                    Operation = Arg.Fallback
                    Keyword = Operation
                    Code += f'Element =  (new { Operation });\npush [my Elements] Element;\n'
                else:
                    raise Exception(f'unexpected statements argument { Arg.Enquote(Arg.Get_Input()) }')
        self.Fallback = Code

class Statement_Statements(Dialect_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'statements' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        Arg = None
        Tail = None
        Statement = 'ERROR_UNKNOWN_STATEMENT'
        Keyword = 'ERROR_UNKNOWN_KEYWORD'
        Code = ''
        for Tail in self.Arguments:
            for Arg in Tail.Elements:
                if isinstance(Arg, Token_Comma):
                    Statement = 'ERROR_UNKNOWN_STATEMENT'
                    Keyword = 'ERROR_UNKNOWN_KEYWORD'
                    continue
                if isinstance(Arg, Token_Quote):
                    Keyword = Arg.Fallback
                    Code += f'[my Statements] { Keyword } d= Element;\ni Add_Keywords { Keyword };\n'
                elif isinstance(Arg, Token_Word):
                    Statement = Arg.Fallback
                    Code += f'Element =  (new { Statement });\npush [my Elements] Element;\n'
                else:
                    raise Exception(f'unexpected statements argument { Arg.Enquote(Arg.Get_Input()) }')
        self.Fallback = Code

class Statement_Syntaxes(Dialect_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'syntaxes' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        Arg = None
        Tail = None
        Syntax = 'ERROR_UNKNOWN_SYNTAX'
        Keyword = 'ERROR_UNKNOWN_KEYWORD'
        Code = ''
        for Tail in self.Arguments:
            for Arg in Tail.Elements:
                if isinstance(Arg, Token_Comma):
                    Syntax = 'ERROR_UNKNOWN_STATEMENT'
                    Keyword = 'ERROR_UNKNOWN_KEYWORD'
                    continue
                if isinstance(Arg, Token_Quote):
                    Keyword = Arg.Fallback
                    Code += f'[my Syntaxes] { Keyword } d= Element;\ni Add_Keywords { Keyword };\n'
                elif isinstance(Arg, Token_Word):
                    Syntax = Arg.Fallback
                    Code += f'Element =  (new { Syntax });\npush [my Elements] Element;\n'
                else:
                    raise Exception(f'unexpected statements argument { Arg.Enquote(Arg.Get_Input()) }')
        self.Fallback = Code

class Statement_Sequence(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'sequence' # string
        self.Rule_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Rule_Name')
        self.Rule_Name = self.Listargs.pop(0)
        self.Rule_Name.Value = 'method'
        self.Rule_Name.Usage = 'method'
        return 1
    def Infer_Fallback(self):
        Verbose = False
        Rule_Name = str(self.Rule_Name.Fallback)
        Declarations = ''
        First = False
        Block = f'comment { self.Enquote(self.Get_Input()) };\ninteger Start_Char = [my Char_Pos];\ninteger Start_Token = [my Token_Pos];\nglobal list My_Elements;\n'
        if Verbose:
            Block += 'verbosity [true];\n'
            Block += f'verbose "Parsing sequence { Rule_Name }.";\n'
        Argument = None
        Excludes = False
        for Argument in self.Listargs:
            try:
                if Argument.Fallback_Declaration is None:
                    raise ValueError
                Declarations += str(Argument.Fallback_Declaration)
            except (ValueError, AttributeError):
                pass
            if isinstance(Argument, (Token_Quote, Syntax_Line, Syntax_Tab)):
                Text = str(Argument.Fallback)
                Block += f'if (not (i Parse_Token My_Elements { Text })) {{ i Rollback Start_Char Start_Token (append "{ self.Rule_Name.Fallback } expected "{ Text }"."); return [false]; }}\n'
                if Verbose:
                    Block += f'verbose [indent] "Sequence { Rule_Name } parsed literal: { Text }";\n'
            elif isinstance(Argument, Token):
                Name = str(Argument.Fallback)
                Block += f'if (not (i Parse_{ Name } My_Elements)) {{ i Rollback Start_Char Start_Token "{ self.Rule_Name.Fallback } expected { Name }."; return [false]; }}\n'
                if Verbose:
                    Block += f'verbose [indent] "Sequence { Rule_Name } parsed token { Name }";\n'
            elif isinstance(Argument, Syntax_Exclude):
                Excludes = True
                Block += f'{ Argument.Fallback }\n'
                if Verbose:
                    Block += f'verbose [indent] "Sequence { Rule_Name } parsed exclude: { Argument.Rule_Name.Input }";\n'
            else:
                Block += f'{ Argument.Fallback }\n'
                if Verbose:
                    Block += f'verbose [indent] "Sequence { Rule_Name } parsed rule: { Argument.Rule_Name.Fallback }";\n'
        if Verbose:
            Block += f'verbose "Sequence { Rule_Name } success, start " Start_Char;\n'
        Block += f'integer End [my Char_Pos];\nobject Element (new { Rule_Name });\nobject First_Child (lget [my Tokens] Start_Token);\nStart_Char = [First_Child.Start_Position];\nElement.Start_Position = Start_Char;\nElement.End_Position = End;\nElement.Document = [self];\ncopy [Element.Elements] = My_Elements;\ni Add_Element Element;\npush Parent_Elements Element;\nreturn [true];\n'
        if Excludes:
            Block = f'list Excluded;\n{ Block }'
        Block = self.Indent(Block)
        Wrapper = str(self.Indent(self.Fallback_Memo_Wrapper(Rule_Name)))
        Code = f'method flag Parse_{ Rule_Name } [list Parent_Elements]\n{{\n{ Wrapper }}}\nmethod flag Parse_{ Rule_Name }_Rule [list Parent_Elements]\n{{\n{ Block }}}'
        self.Fallback_Declarations = Declarations
        self.Fallback = Code

class Statement_Tokens(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'tokens' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        Verbose = False
        Code = ''
        Argument = None
        Between = ''
        Declaration = ''
        D = ''
        for Argument in self.Arguments:
            Name = str(Argument.Fallback)
            Code += f'{ Between }method flag Parse_{ Name } [list Parent_Elements]\n{{\n    object Top_Token (i Top_Token);\n    quit : (isnull Top_Token) [false];\n    if (not (isa Top_Token { Name })) {{ Top_Token.Error = "Expected { Name }";\nreturn [false]; }}\n    push Parent_Elements Top_Token;\n    Top_Token.Error = [null];\n    i Consume_Token;\n    return [true];\n}}'
            Between = '\n'
        self.Fallback = Code

class Statement_Token(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'token' # string
        self.Class_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Class_Name')
        self.Class_Name = self.Listargs.pop(0)
        self.Class_Name.Value = 'class'
        self.Class_Name.Usage = 'class'
        return 1
    def Infer_Fallback(self):
        Verbose = False
        Name = str(self.Class_Name.Fallback)
        Code = f'method flag Parse_{ Name } [list Parent_Elements]\n{{\n    object Top_Token (i Top_Token);\n    return [false] if (isnull Top_Token);\n    if (not (isa Top_Token { Name })) {{ Top_Token.Error = "Expected { Name }";\nreturn [false]; }}\n    push Parent_Elements Top_Token;\n    Top_Token.Error = [null];\n    i Consume_Token;\n    return [true];\n}}'
        self.Fallback = Code
        Declaration = f'class set { Name } {{ property flag Isa_{ Name } [true]; }}\n'
        if Verbose:
            print(f'token declaration: { Declaration }')
        self.Fallback_Declaration = Declaration

class Operation_Flag(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'flag' # string
        self.Op1 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'flag'
        self.Op1.Usage = 'value'
        return 1

class Operation_Number(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'number' # string
        self.Op1 = None # object
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'number'
        self.Op1.Usage = 'value'
        return 1

class Operation_String(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'string' # string
        self.Op1 = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'string'
        self.Op1.Usage = 'value'
        return 1

class Operation_Integer(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'integer' # string
        self.Op1 = None # object
        self.Data_Type = 'integer' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'integer'
        self.Op1.Usage = 'value'
        return 1

class Syntax_Optional(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'optional' # string
        self.Rule_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Rule_Name')
        self.Rule_Name = self.Listargs.pop(0)
        self.Rule_Name.Value = 'method'
        self.Rule_Name.Usage = 'method'
        return 1
    def Infer_Fallback(self):
        Declarations = ''
        Rule = str(self.Rule_Name.Fallback)
        Self_Call = f'i Parse_{ Rule } My_Elements;'
        if isinstance(self.Rule_Name, (Token_Quote, Syntax_Line)):
            Self_Call = f'i Parse_Token My_Elements { Rule };'
            try:
                if self.Rule_Name.Fallback_Declaration is None:
                    raise ValueError
                Declarations += str(self.Rule_Name.Fallback_Declaration)
            except (ValueError, AttributeError):
                pass
        Code = f'comment `optional { Rule }`;\n{ Self_Call }'
        self.Fallback_Declaration = Declarations
        self.Fallback = Code

class Syntax_Optrep(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'optrep' # string
        self.Rule_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Rule_Name')
        self.Rule_Name = self.Listargs.pop(0)
        self.Rule_Name.Value = 'method'
        self.Rule_Name.Usage = 'method'
        return 1
    def Infer_Fallback(self):
        Declarations = ''
        Rule = str(self.Rule_Name.Fallback)
        Defines = ''
        Self_Call = f'(i Parse_{ Rule } My_Elements)'
        if isinstance(self.Rule_Name, (Token_Quote, Syntax_Line)):
            Self_Call = f'(i Parse_Token My_Elements { Rule })'
            try:
                if self.Rule_Name.Fallback_Declaration is None:
                    raise ValueError
                Declarations += str(self.Rule_Name.Fallback_Declaration)
            except (ValueError, AttributeError):
                pass
        Code = f'comment { self.Enquote(self.Get_Input()) };\nforever\n{{\n    break if (not { Self_Call });\n}}'
        try:
            if self.Rule_Name.Fallback_Declaration is None:
                raise ValueError
            self.Fallback_Declaration = self.Rule_Name.Fallback_Declaration
        except (ValueError, AttributeError):
            pass
        self.Fallback_Declaration = Declarations
        self.Fallback = Code

class Syntax_Repeating(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'repeating' # string
        self.Rule_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Rule_Name')
        self.Rule_Name = self.Listargs.pop(0)
        self.Rule_Name.Value = 'method'
        self.Rule_Name.Usage = 'method'
        return 1
    def Infer_Fallback(self):
        Declarations = ''
        Rule = str(self.Rule_Name.Fallback)
        Self_Call = f'(i Parse_{ Rule } My_Elements)'
        if isinstance(self.Rule_Name, (Token_Quote, Syntax_Line)):
            Self_Call = f'(i Parse_Token My_Elements { Rule })'
        try:
            if self.Rule_Name.Fallback_Declaration is None:
                raise ValueError
            Declarations += str(self.Rule_Name.Fallback_Declaration)
        except (ValueError, AttributeError):
            pass
        Code = f'comment `repeating { Rule }`;\nif (not { Self_Call })\n{{\n    i Rollback Start_Char Start_Token `[repeating { Rule }] expected at least one { Rule }.`;\n    return [false];\n}}\nforever\n{{\n    break if (not { Self_Call });\n}}'
        self.Fallback_Declaration = Declarations
        self.Fallback = Code

class Syntax_Sequence(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'sequence' # string
        self.Rule_Name = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Rule_Name')
        self.Rule_Name = self.Listargs.pop(0)
        self.Rule_Name.Value = 'method'
        self.Rule_Name.Usage = 'method'
        return 1
    def Infer_Fallback(self):
        import pdebug; pdebug.zbreak()
        Declarations = ''
        # TODO: the fallback is a reference to the named rule created by this syntax.
        # TODO: the fallback declaration is the sequence function generated by this code.
        My_Source = str(self.Get_Input())
        Rule_Name = str(self.Rule_Name.Fallback)
        Block = f'comment { self.Enquote(self.Get_Input()) };\ninteger Start_Char [my Char_Pos];\ninteger Start_Token [my Token_Pos];\nglobal list My_Elements;\n'
        Argument = None
        Excludes = False
        for Argument in self.Listargs:
            try:
                if Argument.Fallback_Declaration is None:
                    raise ValueError
                Declarations += str(Argument.Fallback_Declaration)
            except (ValueError, AttributeError):
                pass
            if isinstance(Argument, (Token_Quote, Syntax_Line)):
                Text = str(Argument.Fallback)
                Block += f'if (not (i Parse_Token My_Elements { Text })) {{ i Rollback Start_Char Start_Token (append "{ self.Rule_Name.Fallback } expected "{ Text }"."); return [false]; }}\n'
            elif isinstance(Argument, Token):
                Name = str(Argument.Fallback)
                Block += f'if (not (i Parse_{ Name } My_Elements)) {{ i Rollback Start_Char Start_Token "{ self.Rule_Name.Fallback } expected { Name }."; return [false]; }}\n'
            elif isinstance(Argument, Syntax_Exclude):
                Excludes = True
                Block += f'{ Argument.Fallback }\n'
            else:
                Block += f'{ Argument.Fallback }\n'
        Block += f'integer End [my Char_Pos];\nobject Element = (new { self.Rule_Name.Fallback });\nobject First_Child = (lget [my Tokens] Start_Token);\nStart_Char = [First_Child.Start_Position];\nElement.Start_Position = Start_Char;\nElement.End_Position = End;\nElement.Document = [self];\ncopy [Element.Elements] = My_Elements;\ni Add_Element Element;\npush Parent_Elements Element;\nreturn [true];\n'
        if Excludes:
            Block = f'list Excluded;\n{ Block }'
        Block = self.Indent(Block)
        Code = f'{ Declarations }method flag Parse_{ Rule_Name } [list Parent_Elements]\n{{\n{ Block }}}'
        self.Fallback_Declaration = Code
        self.Fallback = Rule_Name

class Syntax_Exclude(Syntax):
    def __init__(self):
        super().__init__()
        self.Keyword = 'exclude' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        import pdebug; pdebug.zbreak()
        Declarations = ''
        Args = str(self.Fallback_Args())
        Code = f'comment { self.Enquote(self.Get_Input()) };\n'
        Argument = None
        for Argument in self.Arguments:
            try:
                if Argument.Fallback_Declaration is None:
                    raise ValueError
                Declarations += str(Argument.Fallback_Declaration)
            except (ValueError, AttributeError):
                pass
            # rule name tokens are required here, right?
            Code += f'return [false] if (i Parse_{ Argument.Fallback } Excluded);\n'
        self.Fallback_Declaration = Declarations
        self.Fallback = Code

class Statement_Symbol(Derived_Class_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'symbol' # string
        self.Type = None # object
        self.Name = None # object
        self.Parent_Class = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required keyword Type')
        self.Type = self.Listargs.pop(0)
        self.Type.Usage = 'type'
        self.Type.Value = 'type'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Name')
        self.Name = self.Listargs.pop(0)
        self.Name.Value = 'class'
        self.Name.Usage = 'class'
        if len(self.Listargs) > 0:
            self.Parent_Class = self.Listargs.pop(0)
            self.Parent_Class.Value = 'class'
            self.Parent_Class.Usage = 'class'
        return 1
    def Infer_Fallback(self):
        Type = str(self.Type.Fallback)
        Name = str(self.Name.Fallback)
        Parent_Class = 'Symbol'
        try:
            if self.Parent_Class.Fallback is None:
                raise ValueError
            Parent_Class = self.Parent_Class.Fallback
        except (ValueError, AttributeError):
            pass
        Block = ''
        Declaration = ''
        try:
            for Statement in self.Block.Statements:
                try:
                    if Statement.Fallback_Declaration is None:
                        raise ValueError
                    Declaration += str(Statement.Fallback_Declaration)
                except (ValueError, AttributeError):
                    pass
        except Exception: pass
        Default_Value = f' [{ Type } Value [null]]'
        Initializer = f"    if (Value ne [null]) {{\n{ '    ' * 3 }my Symbol_Value = Value;\n{ '    ' * 2 }}}\n    "
        if f' { Type } ' in ' list dictionary object glvn dict ':
            Default_Value = ''
            Initializer = ''
        Code = f"{ Declaration }\nclass { Name } is { Parent_Class }\n{{\n    property object Symbol_Object;\n    property { Type } Symbol_Value;\n    constructor [object Object]{ Default_Value }\n    {{\n{ '    ' * 2 }my Symbol_Object = Object;\n    { Initializer }}}\n{ Block }}}"
        self.Fallback = Code

class Operation_Join(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'join' # string
        self.List = None # object
        self.Separator = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Separator')
        self.Separator = self.Listargs.pop(0)
        self.Separator.Value = 'string'
        self.Separator.Usage = 'value'
        return 1

class Statement_Break(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'break' # string
    def Attributes(self):
        return 1

class Statement_Break_If(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'break if' # string
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Condition')
        self.Condition = self.Listargs.pop(0)
        self.Condition.Value = 'flag'
        self.Condition.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'if{ self.Fallback_Arguments() } {{ break; }}'
        self.Fallback = Code

class Statement_Replace(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'replace' # string
        self.Variable = None # object
        self.Search_Text = None # object
        self.Replace_Text = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'string'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Search_Text')
        self.Search_Text = self.Listargs.pop(0)
        self.Search_Text.Value = 'string'
        self.Search_Text.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Replace_Text')
        self.Replace_Text = self.Listargs.pop(0)
        self.Replace_Text.Value = 'string'
        self.Replace_Text.Usage = 'value'
        return 1

class Statement_List_Clear(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'lclear' # string
        self.List = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument List')
        self.List = self.Listargs.pop(0)
        self.List.Value = 'list'
        self.List.Usage = 'varaible'
        return 1

# ****************************************************************************************************************
# * python-specific language elements, the targets of python-to-gal translation. each carries python semantics and lowers to gal atomics in the fallback generators, so only atomic constructs ever need a new target-language backend. *
# ****************************************************************************************************************
class Statement_Python_Print(Append_Args_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'python print' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        # python print separates its arguments with single spaces
        Code = 'say'
        First = True
        Arg = None
        for Arg in self.Arguments:
            if not First:
                Code += " ' '"
            Code += f' { Arg.Fallback }'
            First = False
        Code += ';'
        self.Fallback = Code

class Statement_Python_While(If_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'python while' # string
        self.Condition = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Condition')
        self.Condition = self.Listargs.pop(0)
        self.Condition.Value = 'flag'
        self.Condition.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        # gal has no while loop: forever with an inverted break
        Code = f'forever\n{{\n    break if (not { self.Condition.Fallback });\n{ self.Fallback_Statements() }}}'
        self.Fallback = Code

class Statement_Python_Print0(Append_Args_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'python print0' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        # python print with sep=’’: plain say, no separators
        Code = f'say{ self.Fallback_Arguments() };'
        self.Fallback = Code

class Statement_Python_For_Range(For_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'python for range' # string
        self.Variable = None # object
        self.Limit = None # object
        self.Upper = None # object
    # one argument: range(Limit), zero to Limit - 1. two arguments:
    #     range(Limit, Upper), Limit to Upper - 1.
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Variable')
        self.Variable = self.Listargs.pop(0)
        self.Variable.Value = 'number'
        self.Variable.Usage = 'variable'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Limit')
        self.Limit = self.Listargs.pop(0)
        self.Limit.Value = 'number'
        self.Limit.Usage = 'value'
        if len(self.Listargs) > 0:
            self.Upper = self.Listargs.pop(0)
            self.Upper.Value = 'number'
            self.Upper.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'for { self.Variable.Fallback } range '
        if self.Upper is not None:
            # two-argument range: Limit is the start, Upper the end
            Code += f'{ self.Limit.Fallback } ({ self.Upper.Fallback } - 1)'
        else:
            Code += f'0 ({ self.Limit.Fallback } - 1)'
        Code += str(self.Fallback_Block())
        self.Fallback = Code

class Statement_Python_Setitem(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'python setitem' # string
        self.Target = None # object
        self.Key = None # object
        self.Value = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Target')
        self.Target = self.Listargs.pop(0)
        self.Target.Value = 'variant'
        self.Target.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Key')
        self.Key = self.Listargs.pop(0)
        self.Key.Value = 'variant'
        self.Key.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Value')
        self.Value = self.Listargs.pop(0)
        self.Value.Value = 'variant'
        self.Value.Usage = 'value'
        return 1

class Statement_Python_Raise(Line_Statement):
    def __init__(self):
        super().__init__()
        self.Keyword = 'python raise' # string
        self.Message = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Message')
        self.Message = self.Listargs.pop(0)
        self.Message.Value = 'variant'
        self.Message.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'error { self.Message.Fallback };'
        self.Fallback = Code

class Operation_Python_Add(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py +' # string
        self.Op1 = None # object
        self.Op2 = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        # python’s + concatenates when a string is involved and
        #         adds otherwise; the inferred types choose between the append
        #         operation and numeric +. unknown and variant operands keep the
        #         numeric form, matching the python behavior for numbers.
        Stringish = False
        if str(self.Fallback_Arg_Data_Type(self.Op1)) == 'string':
            Stringish = True
        if str(self.Fallback_Arg_Data_Type(self.Op2)) == 'string':
            Stringish = True
        # record the decision as this operation’s own data type:
        #         operands lower before the operations that contain them, so an
        #         enclosing py + reads a chained operand’s resolved type in the
        #         same pass
        if Stringish:
            self.Data_Type = 'string'
            self.Fallback = f'(append { self.Op1.Fallback } { self.Op2.Fallback })'
        else:
            self.Data_Type = 'number'
            self.Fallback = f'({ self.Op1.Fallback } + { self.Op2.Fallback })'

class Operation_Python_Sub(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py -' # string
        self.Op1 = None # object
        self.Op2 = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } - { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Mul(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py *' # string
        self.Op1 = None # object
        self.Op2 = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } * { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Div(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py /' # string
        self.Op1 = None # object
        self.Op2 = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } / { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Mod(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py mod' # string
        self.Op1 = None # object
        self.Op2 = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } mod { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Lt(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py <' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } < { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Gt(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py >' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } > { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Le(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py <=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } <= { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Ge(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py >=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } >= { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Eq(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py =' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } = { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Ne(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py !=' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } != { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_And(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py and' # string
        self.Op1 = None # object
        self.Op2 = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } and { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Or(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py or' # string
        self.Op1 = None # object
        self.Op2 = None # object
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } or { self.Op2.Fallback })'
        self.Fallback = Code

class Operation_Python_Not(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py not' # string
        self.Op1 = None # object
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'(not { self.Op1.Fallback })'
        self.Fallback = Code

class Operation_Python_Neg(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py neg' # string
        self.Op1 = None # object
        self.Data_Type = 'number' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'(0 - { self.Op1.Fallback })'
        self.Fallback = Code

class Operation_Python_Str(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py str' # string
        self.Op1 = None # object
        self.Data_Type = 'string' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'(string { self.Op1.Fallback })'
        self.Fallback = Code

class Operation_Python_Len(Unary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py len' # string
        self.Op1 = None # object
        self.Python_Precedence = 1 # integer
        self.Javascript_Precedence = 1 # integer
        self.Data_Type = 'integer' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        return 1

class Operation_Python_In(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py in' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1

class Operation_Python_Is(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py is' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1

class Operation_Python_Is_Not(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py is not' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1

class Operation_Python_Subscript(Binary_Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py sub' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Python_Precedence = 1 # integer
        self.Javascript_Precedence = 1 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        return 1

class Operation_Python_Isa(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py isa' # string
        self.Op1 = None # object
        self.Python_Precedence = 11 # integer
        self.Javascript_Precedence = 11 # integer
        self.Data_Type = 'flag' # string
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        return 1
    def Infer_Fallback(self):
        Code = f'({ self.Op1.Fallback } is a'
        Arg = None
        First = True
        for Arg in self.Arguments:
            if First:
                First = False
                continue
            Code += f' { Arg.Fallback }'
        Code += ')'
        self.Fallback = Code

class Operation_Python_Slice(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py slice' # string
        self.Op1 = None # object
        self.Op2 = None # object
        self.Op3 = None # object
        self.Python_Precedence = 1 # integer
        self.Javascript_Precedence = 1 # integer
    def Attributes(self):
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op1')
        self.Op1 = self.Listargs.pop(0)
        self.Op1.Value = 'variant'
        self.Op1.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op2')
        self.Op2 = self.Listargs.pop(0)
        self.Op2.Value = 'variant'
        self.Op2.Usage = 'value'
        if len(self.Listargs) == 0:
            raise Exception('missing required argument Op3')
        self.Op3 = self.Listargs.pop(0)
        self.Op3.Value = 'variant'
        self.Op3.Usage = 'value'
        return 1

class Operation_Python_Fstr(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py fstr' # string
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
        self.Data_Type = 'string' # string
    def Attributes(self):
        return 1
    def Infer_Fallback(self):
        # a python f-string: an append of literal and expression
        #         segments, which the target generators render back as an f-string
        Code = f'(append{ self.Fallback_Arguments() })'
        self.Fallback = Code

class Operation_Python_List_Literal(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py list' # string
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
        self.Data_Type = 'list' # string
    def Attributes(self):
        return 1

class Operation_Python_Tuple_Literal(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py tuple' # string
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
        self.Data_Type = 'list' # string
    def Attributes(self):
        return 1

class Operation_Python_Dict_Literal(Operation):
    def __init__(self):
        super().__init__()
        self.Keyword = 'py dict' # string
        self.Python_Precedence = 2 # integer
        self.Javascript_Precedence = 2 # integer
        self.Data_Type = 'dictionary' # string
    def Attributes(self):
        return 1

class Dialect_Compiler(Dialect):
    def Initialize(self):
        Element = None
        self.Name = 'Compiler'
        # ENGLISH: the compiler dialect includes the optimal set of language elements to support the gal compiler.
        Element = Statement_Add()
        self.Elements.extend([Element])
        self.Statements['+'] = Element
        self.Add_Keywords('+')
        self.Statements['add'] = Element
        self.Add_Keywords('add')
        self.Statements['+='] = Element
        self.Add_Keywords('+=')
        self.Statements['+ ='] = Element
        self.Add_Keywords('+ =')
        Element = Statement_Append()
        self.Elements.extend([Element])
        self.Statements['append'] = Element
        self.Add_Keywords('append')
        self.Statements['s+'] = Element
        self.Add_Keywords('s+')
        self.Statements['s +'] = Element
        self.Add_Keywords('s +')
        Element = Statement_Argument()
        self.Elements.extend([Element])
        self.Statements['argument'] = Element
        self.Add_Keywords('argument')
        Element = Statement_Assign()
        self.Elements.extend([Element])
        self.Statements['='] = Element
        self.Add_Keywords('=')
        Element = Statement_Break()
        self.Elements.extend([Element])
        self.Statements['break'] = Element
        self.Add_Keywords('break')
        Element = Statement_Break_If()
        self.Elements.extend([Element])
        self.Statements['break if'] = Element
        self.Add_Keywords('break if')
        self.Statements['breakif'] = Element
        self.Add_Keywords('breakif')
        Element = Statement_Call()
        self.Elements.extend([Element])
        self.Statements['.'] = Element
        self.Add_Keywords('.')
        Element = Statement_Catch()
        self.Elements.extend([Element])
        self.Statements['catch'] = Element
        self.Add_Keywords('catch')
        Element = Statement_Class()
        self.Elements.extend([Element])
        self.Statements['class'] = Element
        self.Add_Keywords('class')
        self.Statements['class is'] = Element
        self.Add_Keywords('class is')
        Element = Statement_Class_Method()
        self.Elements.extend([Element])
        self.Statements['class method'] = Element
        self.Add_Keywords('class method')
        self.Statements['static method'] = Element
        self.Add_Keywords('static method')
        Element = Statement_Class_Property()
        self.Elements.extend([Element])
        self.Statements['class property'] = Element
        self.Add_Keywords('class property')
        self.Statements['static property'] = Element
        self.Add_Keywords('static property')
        self.Statements['class property ='] = Element
        self.Add_Keywords('class property =')
        self.Statements['static property ='] = Element
        self.Add_Keywords('static property =')
        Element = Statement_Class_Set()
        self.Elements.extend([Element])
        self.Statements['class set'] = Element
        self.Add_Keywords('class set')
        self.Statements['class append'] = Element
        self.Add_Keywords('class append')
        Element = Statement_Colon()
        self.Elements.extend([Element])
        self.Statements[':'] = Element
        self.Add_Keywords(':')
        Element = Statement_Comment()
        self.Elements.extend([Element])
        self.Statements['#'] = Element
        self.Add_Keywords('#')
        self.Statements['comment'] = Element
        self.Add_Keywords('comment')
        self.Statements['//'] = Element
        self.Add_Keywords('//')
        self.Statements['/ /'] = Element
        self.Add_Keywords('/ /')
        Element = Statement_Constructor()
        self.Elements.extend([Element])
        self.Statements['constructor'] = Element
        self.Add_Keywords('constructor')
        Element = Statement_Continue()
        self.Elements.extend([Element])
        self.Statements['continue'] = Element
        self.Add_Keywords('continue')
        Element = Statement_Continue_If()
        self.Elements.extend([Element])
        self.Statements['continue if'] = Element
        self.Add_Keywords('continue if')
        self.Statements['if continue'] = Element
        self.Add_Keywords('if continue')
        self.Statements['contif'] = Element
        self.Add_Keywords('contif')
        Element = Statement_Debug()
        self.Elements.extend([Element])
        self.Statements['debug'] = Element
        self.Add_Keywords('debug')
        Element = Statement_Debug_If()
        self.Elements.extend([Element])
        self.Statements['debug if'] = Element
        self.Add_Keywords('debug if')
        Element = Statement_Decrement()
        self.Elements.extend([Element])
        self.Statements['decrement'] = Element
        self.Add_Keywords('decrement')
        self.Statements['--'] = Element
        self.Add_Keywords('--')
        self.Statements['- -'] = Element
        self.Add_Keywords('- -')
        Element = Statement_Defined()
        self.Elements.extend([Element])
        self.Statements['defined'] = Element
        self.Add_Keywords('defined')
        Element = Statement_Dialect()
        self.Elements.extend([Element])
        self.Statements['dialect'] = Element
        self.Add_Keywords('dialect')
        Element = Statement_Dictionary()
        self.Elements.extend([Element])
        self.Statements['dict'] = Element
        self.Add_Keywords('dict')
        self.Statements['dictionary'] = Element
        self.Add_Keywords('dictionary')
        Element = Statement_Dictionary_Assign()
        self.Elements.extend([Element])
        self.Statements['dict ='] = Element
        self.Add_Keywords('dict =')
        self.Statements['d ='] = Element
        self.Add_Keywords('d =')
        self.Statements['d='] = Element
        self.Add_Keywords('d=')
        Element = Statement_Either()
        self.Elements.extend([Element])
        self.Statements['either'] = Element
        self.Add_Keywords('either')
        Element = Statement_Else()
        self.Elements.extend([Element])
        self.Statements['else'] = Element
        self.Add_Keywords('else')
        Element = Statement_Else_If()
        self.Elements.extend([Element])
        self.Statements['else if'] = Element
        self.Add_Keywords('else if')
        Element = Statement_English()
        self.Elements.extend([Element])
        self.Statements['english'] = Element
        self.Add_Keywords('english')
        Element = Statement_Entity()
        self.Elements.extend([Element])
        self.Statements['entity'] = Element
        self.Add_Keywords('entity')
        Element = Statement_Error()
        self.Elements.extend([Element])
        self.Statements['error'] = Element
        self.Add_Keywords('error')
        Element = Statement_File_Read()
        self.Elements.extend([Element])
        self.Statements['fread'] = Element
        self.Add_Keywords('fread')
        self.Statements['file read all'] = Element
        self.Add_Keywords('file read all')
        Element = Statement_Flag()
        self.Elements.extend([Element])
        self.Statements['flag'] = Element
        self.Add_Keywords('flag')
        self.Statements['flag ='] = Element
        self.Add_Keywords('flag =')
        Element = Statement_Flags()
        self.Elements.extend([Element])
        self.Statements['flags'] = Element
        self.Add_Keywords('flags')
        Element = Statement_Flowerbox()
        self.Elements.extend([Element])
        self.Statements['flowerbox'] = Element
        self.Add_Keywords('flowerbox')
        self.Statements['flower box'] = Element
        self.Add_Keywords('flower box')
        Element = Statement_For_Each()
        self.Elements.extend([Element])
        self.Statements['for each'] = Element
        self.Add_Keywords('for each')
        self.Statements['foreach'] = Element
        self.Add_Keywords('foreach')
        Element = Statement_For_Each_In()
        self.Elements.extend([Element])
        self.Statements['for each in'] = Element
        self.Add_Keywords('for each in')
        Element = Statement_For_Range()
        self.Elements.extend([Element])
        self.Statements['for range'] = Element
        self.Add_Keywords('for range')
        self.Statements['for range'] = Element
        self.Add_Keywords('for range')
        Element = Statement_Forever()
        self.Elements.extend([Element])
        self.Statements['forever'] = Element
        self.Add_Keywords('forever')
        Element = Statement_Forgive()
        self.Elements.extend([Element])
        self.Statements['forgive'] = Element
        self.Add_Keywords('forgive')
        self.Statements['try catch'] = Element
        self.Add_Keywords('try catch')
        Element = Statement_Generate()
        self.Elements.extend([Element])
        self.Statements['generate'] = Element
        self.Add_Keywords('generate')
        Element = Statement_Generator()
        self.Elements.extend([Element])
        self.Statements['generator'] = Element
        self.Add_Keywords('generator')
        Element = Statement_Global_List()
        self.Elements.extend([Element])
        self.Statements['global list'] = Element
        self.Add_Keywords('global list')
        Element = Statement_Handle()
        self.Elements.extend([Element])
        self.Statements['handle'] = Element
        self.Add_Keywords('handle')
        Element = Statement_I()
        self.Elements.extend([Element])
        self.Statements['i'] = Element
        self.Add_Keywords('i')
        Element = Statement_I_Equal()
        self.Elements.extend([Element])
        self.Statements['i ='] = Element
        self.Add_Keywords('i =')
        Element = Statement_If()
        self.Elements.extend([Element])
        self.Statements['if'] = Element
        self.Add_Keywords('if')
        Element = Statement_If_Return()
        self.Elements.extend([Element])
        self.Statements['if return'] = Element
        self.Add_Keywords('if return')
        self.Statements['quit :'] = Element
        self.Add_Keywords('quit :')
        self.Statements['quit:'] = Element
        self.Add_Keywords('quit:')
        Element = Statement_Include()
        self.Elements.extend([Element])
        self.Statements['include'] = Element
        self.Add_Keywords('include')
        Element = Statement_Increment()
        self.Elements.extend([Element])
        self.Statements['increment'] = Element
        self.Add_Keywords('increment')
        self.Statements['++'] = Element
        self.Add_Keywords('++')
        self.Statements['+ +'] = Element
        self.Add_Keywords('+ +')
        Element = Statement_Inference()
        self.Elements.extend([Element])
        self.Statements['inference'] = Element
        self.Add_Keywords('inference')
        Element = Statement_Integer()
        self.Elements.extend([Element])
        self.Statements['integer'] = Element
        self.Add_Keywords('integer')
        self.Statements['integer ='] = Element
        self.Add_Keywords('integer =')
        Element = Statement_Integers()
        self.Elements.extend([Element])
        self.Statements['integers'] = Element
        self.Add_Keywords('integers')
        Element = Statement_Iterate()
        self.Elements.extend([Element])
        self.Statements['iterate'] = Element
        self.Add_Keywords('iterate')
        Element = Statement_Join()
        self.Elements.extend([Element])
        self.Statements['join'] = Element
        self.Add_Keywords('join')
        Element = Statement_Keyword()
        self.Elements.extend([Element])
        self.Statements['keyword'] = Element
        self.Add_Keywords('keyword')
        Element = Statement_List()
        self.Elements.extend([Element])
        self.Statements['list'] = Element
        self.Add_Keywords('list')
        Element = Statement_List_Clear()
        self.Elements.extend([Element])
        self.Statements['lclear'] = Element
        self.Add_Keywords('lclear')
        Element = Statement_List_Copy()
        self.Elements.extend([Element])
        self.Statements['list copy'] = Element
        self.Add_Keywords('list copy')
        self.Statements['list copy of'] = Element
        self.Add_Keywords('list copy of')
        self.Statements['copy ='] = Element
        self.Add_Keywords('copy =')
        Element = Statement_List_Split()
        self.Elements.extend([Element])
        self.Statements['list split'] = Element
        self.Add_Keywords('list split')
        self.Statements['lsplit'] = Element
        self.Add_Keywords('lsplit')
        self.Statements['split'] = Element
        self.Add_Keywords('split')
        Element = Statement_Main()
        self.Elements.extend([Element])
        self.Statements['main'] = Element
        self.Add_Keywords('main')
        Element = Statement_Method()
        self.Elements.extend([Element])
        self.Statements['method'] = Element
        self.Add_Keywords('method')
        Element = Statement_Module()
        self.Elements.extend([Element])
        self.Statements['module'] = Element
        self.Add_Keywords('module')
        Element = Statement_My_Equal()
        self.Elements.extend([Element])
        self.Statements['my ='] = Element
        self.Add_Keywords('my =')
        Element = Statement_Number()
        self.Elements.extend([Element])
        self.Statements['number'] = Element
        self.Add_Keywords('number')
        self.Statements['number ='] = Element
        self.Add_Keywords('number =')
        Element = Statement_Numbers()
        self.Elements.extend([Element])
        self.Statements['numbers'] = Element
        self.Add_Keywords('numbers')
        Element = Statement_Object()
        self.Elements.extend([Element])
        self.Statements['object'] = Element
        self.Add_Keywords('object')
        self.Statements['object ='] = Element
        self.Add_Keywords('object =')
        Element = Statement_Objects()
        self.Elements.extend([Element])
        self.Statements['objects'] = Element
        self.Add_Keywords('objects')
        Element = Statement_Operation()
        self.Elements.extend([Element])
        self.Statements['operation'] = Element
        self.Add_Keywords('operation')
        Element = Statement_Operations()
        self.Elements.extend([Element])
        self.Statements['operations'] = Element
        self.Add_Keywords('operations')
        Element = Statement_Optional()
        self.Elements.extend([Element])
        self.Statements['optional'] = Element
        self.Add_Keywords('optional')
        Element = Statement_Parser()
        self.Elements.extend([Element])
        self.Statements['parser'] = Element
        self.Add_Keywords('parser')
        Element = Statement_Property()
        self.Elements.extend([Element])
        self.Statements['property'] = Element
        self.Add_Keywords('property')
        self.Statements['property ='] = Element
        self.Add_Keywords('property =')
        Element = Statement_Propset()
        self.Elements.extend([Element])
        self.Statements['. ='] = Element
        self.Add_Keywords('. =')
        Element = Statement_Push()
        self.Elements.extend([Element])
        self.Statements['push'] = Element
        self.Add_Keywords('push')
        Element = Statement_Python_For_Range()
        self.Elements.extend([Element])
        self.Statements['python for range'] = Element
        self.Add_Keywords('python for range')
        Element = Statement_Python_Print()
        self.Elements.extend([Element])
        self.Statements['python print'] = Element
        self.Add_Keywords('python print')
        Element = Statement_Python_Print0()
        self.Elements.extend([Element])
        self.Statements['python print0'] = Element
        self.Add_Keywords('python print0')
        Element = Statement_Python_Raise()
        self.Elements.extend([Element])
        self.Statements['python raise'] = Element
        self.Add_Keywords('python raise')
        Element = Statement_Python_Setitem()
        self.Elements.extend([Element])
        self.Statements['python setitem'] = Element
        self.Add_Keywords('python setitem')
        Element = Statement_Python_While()
        self.Elements.extend([Element])
        self.Statements['python while'] = Element
        self.Add_Keywords('python while')
        Element = Statement_Readline()
        self.Elements.extend([Element])
        self.Statements['readline'] = Element
        self.Add_Keywords('readline')
        self.Statements['read line'] = Element
        self.Add_Keywords('read line')
        Element = Statement_Return()
        self.Elements.extend([Element])
        self.Statements['return'] = Element
        self.Add_Keywords('return')
        Element = Statement_Return_If()
        self.Elements.extend([Element])
        self.Statements['return if'] = Element
        self.Add_Keywords('return if')
        self.Statements['returnif'] = Element
        self.Add_Keywords('returnif')
        Element = Statement_Replace()
        self.Elements.extend([Element])
        self.Statements['replace'] = Element
        self.Add_Keywords('replace')
        self.Statements['replace with'] = Element
        self.Add_Keywords('replace with')
        Element = Statement_Say()
        self.Elements.extend([Element])
        self.Statements['say'] = Element
        self.Add_Keywords('say')
        self.Statements['print'] = Element
        self.Add_Keywords('print')
        self.Statements['console'] = Element
        self.Add_Keywords('console')
        self.Statements['write line'] = Element
        self.Add_Keywords('write line')
        Element = Statement_Sequence()
        self.Elements.extend([Element])
        self.Statements['sequence'] = Element
        self.Add_Keywords('sequence')
        Element = Statement_Shell_Capture()
        self.Elements.extend([Element])
        self.Statements['shell capture'] = Element
        self.Add_Keywords('shell capture')
        Element = Statement_Statement()
        self.Elements.extend([Element])
        self.Statements['statement'] = Element
        self.Add_Keywords('statement')
        Element = Statement_Statements()
        self.Elements.extend([Element])
        self.Statements['statements'] = Element
        self.Add_Keywords('statements')
        Element = Statement_String()
        self.Elements.extend([Element])
        self.Statements['string'] = Element
        self.Add_Keywords('string')
        self.Statements['string ='] = Element
        self.Add_Keywords('string =')
        Element = Statement_Strings()
        self.Elements.extend([Element])
        self.Statements['strings'] = Element
        self.Add_Keywords('strings')
        Element = Statement_Super()
        self.Elements.extend([Element])
        self.Statements['super'] = Element
        self.Add_Keywords('super')
        Element = Statement_Symbol()
        self.Elements.extend([Element])
        self.Statements['symbol'] = Element
        self.Add_Keywords('symbol')
        Element = Statement_Syntax()
        self.Elements.extend([Element])
        self.Statements['syntax'] = Element
        self.Add_Keywords('syntax')
        Element = Statement_Syntaxes()
        self.Elements.extend([Element])
        self.Statements['syntaxes'] = Element
        self.Add_Keywords('syntaxes')
        Element = Statement_Todo()
        self.Elements.extend([Element])
        self.Statements['to do'] = Element
        self.Add_Keywords('to do')
        self.Statements['todo'] = Element
        self.Add_Keywords('todo')
        Element = Statement_Tokens()
        self.Elements.extend([Element])
        self.Statements['tokens'] = Element
        self.Add_Keywords('tokens')
        Element = Statement_Try()
        self.Elements.extend([Element])
        self.Statements['try'] = Element
        self.Add_Keywords('try')
        Element = Statement_Undefined()
        self.Elements.extend([Element])
        self.Statements['undefined'] = Element
        self.Add_Keywords('undefined')
        self.Statements['undef'] = Element
        self.Add_Keywords('undef')
        self.Statements['un defined'] = Element
        self.Add_Keywords('un defined')
        Element = Statement_Variant()
        self.Elements.extend([Element])
        self.Statements['variant'] = Element
        self.Add_Keywords('variant')
        self.Statements['variant ='] = Element
        self.Add_Keywords('variant =')
        self.Statements['var'] = Element
        self.Add_Keywords('var')
        Element = Statement_Variants()
        self.Elements.extend([Element])
        self.Statements['variants'] = Element
        self.Add_Keywords('variants')
        self.Statements['vars'] = Element
        self.Add_Keywords('vars')
        Element = Statement_Verbose()
        self.Elements.extend([Element])
        self.Statements['verbose'] = Element
        self.Add_Keywords('verbose')
        Element = Statement_Verbosity()
        self.Elements.extend([Element])
        self.Statements['verbosity'] = Element
        self.Add_Keywords('verbosity')
        Element = Statement_Write_To()
        self.Elements.extend([Element])
        self.Statements['write to'] = Element
        self.Add_Keywords('write to')
        self.Statements['to file'] = Element
        self.Add_Keywords('to file')
        self.Statements['dump to file'] = Element
        self.Add_Keywords('dump to file')
        self.Statements['write to file'] = Element
        self.Add_Keywords('write to file')
        self.Statements['file dump'] = Element
        self.Add_Keywords('file dump')
        Element = Operation_Add()
        self.Elements.extend([Element])
        self.Operations['+'] = Element
        self.Add_Keywords('+')
        Element = Operation_And()
        self.Elements.extend([Element])
        self.Operations['and'] = Element
        self.Add_Keywords('and')
        self.Operations['&'] = Element
        self.Add_Keywords('&')
        Element = Operation_Append()
        self.Elements.extend([Element])
        self.Operations['append'] = Element
        self.Add_Keywords('append')
        self.Operations['s+'] = Element
        self.Add_Keywords('s+')
        self.Operations['s +'] = Element
        self.Add_Keywords('s +')
        Element = Operation_Call()
        self.Elements.extend([Element])
        self.Operations['.'] = Element
        self.Add_Keywords('.')
        Element = Operation_Colon()
        self.Elements.extend([Element])
        self.Operations[':'] = Element
        self.Add_Keywords(':')
        Element = Operation_Contains()
        self.Elements.extend([Element])
        self.Operations['contains'] = Element
        self.Add_Keywords('contains')
        Element = Operation_Defined()
        self.Elements.extend([Element])
        self.Operations['defined'] = Element
        self.Add_Keywords('defined')
        Element = Operation_Dict_Exists()
        self.Elements.extend([Element])
        self.Operations['dexists'] = Element
        self.Add_Keywords('dexists')
        self.Operations['dict exists'] = Element
        self.Add_Keywords('dict exists')
        Element = Operation_Dict_Get()
        self.Elements.extend([Element])
        self.Operations['dget'] = Element
        self.Add_Keywords('dget')
        self.Operations['dict get'] = Element
        self.Add_Keywords('dict get')
        self.Operations['get'] = Element
        self.Add_Keywords('get')
        Element = Operation_Divide()
        self.Elements.extend([Element])
        self.Operations['/'] = Element
        self.Add_Keywords('/')
        Element = Operation_Equal()
        self.Elements.extend([Element])
        self.Operations['='] = Element
        self.Add_Keywords('=')
        self.Operations['eq'] = Element
        self.Add_Keywords('eq')
        Element = Operation_File_Exists()
        self.Elements.extend([Element])
        self.Operations['file exists'] = Element
        self.Add_Keywords('file exists')
        self.Operations['fexists'] = Element
        self.Add_Keywords('fexists')
        Element = Operation_Flag()
        self.Elements.extend([Element])
        self.Operations['flag'] = Element
        self.Add_Keywords('flag')
        Element = Operation_Greater()
        self.Elements.extend([Element])
        self.Operations['>'] = Element
        self.Add_Keywords('>')
        self.Operations['gt'] = Element
        self.Add_Keywords('gt')
        Element = Operation_Greater_Equal()
        self.Elements.extend([Element])
        self.Operations['>='] = Element
        self.Add_Keywords('>=')
        self.Operations['> ='] = Element
        self.Add_Keywords('> =')
        self.Operations['ge'] = Element
        self.Add_Keywords('ge')
        Element = Operation_I()
        self.Elements.extend([Element])
        self.Operations['i'] = Element
        self.Add_Keywords('i')
        self.Operations['self'] = Element
        self.Add_Keywords('self')
        Element = Operation_Integer()
        self.Elements.extend([Element])
        self.Operations['integer'] = Element
        self.Add_Keywords('integer')
        self.Operations['int'] = Element
        self.Add_Keywords('int')
        Element = Operation_Is_A()
        self.Elements.extend([Element])
        self.Operations['is a'] = Element
        self.Add_Keywords('is a')
        self.Operations['isa'] = Element
        self.Add_Keywords('isa')
        self.Operations['is an'] = Element
        self.Add_Keywords('is an')
        self.Operations['isan'] = Element
        self.Add_Keywords('isan')
        Element = Operation_Is_Ident()
        self.Elements.extend([Element])
        self.Operations['is ident'] = Element
        self.Add_Keywords('is ident')
        Element = Operation_Is_Lower()
        self.Elements.extend([Element])
        self.Operations['is lower'] = Element
        self.Add_Keywords('is lower')
        self.Operations['is lowercase'] = Element
        self.Add_Keywords('is lowercase')
        Element = Operation_Is_Not_A()
        self.Elements.extend([Element])
        self.Operations['is not a'] = Element
        self.Add_Keywords('is not a')
        Element = Operation_Is_Null()
        self.Elements.extend([Element])
        self.Operations['isnull'] = Element
        self.Add_Keywords('isnull')
        self.Operations['is null'] = Element
        self.Add_Keywords('is null')
        Element = Operation_Is_Numeric()
        self.Elements.extend([Element])
        self.Operations['is numeric'] = Element
        self.Add_Keywords('is numeric')
        Element = Operation_Is_Punctuation()
        self.Elements.extend([Element])
        self.Operations['is punct'] = Element
        self.Add_Keywords('is punct')
        self.Operations['is punctuation'] = Element
        self.Add_Keywords('is punctuation')
        Element = Operation_Is_Upper()
        self.Elements.extend([Element])
        self.Operations['is upper'] = Element
        self.Add_Keywords('is upper')
        self.Operations['is uppercase'] = Element
        self.Add_Keywords('is uppercase')
        Element = Operation_Is_Whitespace()
        self.Elements.extend([Element])
        self.Operations['is whitespace'] = Element
        self.Add_Keywords('is whitespace')
        Element = Operation_Join()
        self.Elements.extend([Element])
        self.Operations['join'] = Element
        self.Add_Keywords('join')
        Element = Operation_Length()
        self.Elements.extend([Element])
        self.Operations['length'] = Element
        self.Add_Keywords('length')
        Element = Operation_Less()
        self.Elements.extend([Element])
        self.Operations['<'] = Element
        self.Add_Keywords('<')
        self.Operations['lt'] = Element
        self.Add_Keywords('lt')
        Element = Operation_Less_Equal()
        self.Elements.extend([Element])
        self.Operations['<='] = Element
        self.Add_Keywords('<=')
        self.Operations['le'] = Element
        self.Add_Keywords('le')
        self.Operations['< ='] = Element
        self.Add_Keywords('< =')
        Element = Operation_List_Get()
        self.Elements.extend([Element])
        self.Operations['lget'] = Element
        self.Add_Keywords('lget')
        self.Operations['list get'] = Element
        self.Add_Keywords('list get')
        Element = Operation_List_Last()
        self.Elements.extend([Element])
        self.Operations['llast'] = Element
        self.Add_Keywords('llast')
        self.Operations['list last'] = Element
        self.Add_Keywords('list last')
        Element = Operation_List_Length()
        self.Elements.extend([Element])
        self.Operations['llength'] = Element
        self.Add_Keywords('llength')
        self.Operations['list length'] = Element
        self.Add_Keywords('list length')
        Element = Operation_Minus()
        self.Elements.extend([Element])
        self.Operations['-'] = Element
        self.Add_Keywords('-')
        Element = Operation_Modulo()
        self.Elements.extend([Element])
        self.Operations['mod'] = Element
        self.Add_Keywords('mod')
        Element = Operation_Multiply()
        self.Elements.extend([Element])
        self.Operations['*'] = Element
        self.Add_Keywords('*')
        Element = Operation_New()
        self.Elements.extend([Element])
        self.Operations['new'] = Element
        self.Add_Keywords('new')
        Element = Operation_Not()
        self.Elements.extend([Element])
        self.Operations['not'] = Element
        self.Add_Keywords('not')
        self.Operations['!'] = Element
        self.Add_Keywords('!')
        Element = Operation_Not_Equal()
        self.Elements.extend([Element])
        self.Operations['!='] = Element
        self.Add_Keywords('!=')
        self.Operations['ne'] = Element
        self.Add_Keywords('ne')
        self.Operations['! ='] = Element
        self.Add_Keywords('! =')
        Element = Operation_Not_Null()
        self.Elements.extend([Element])
        self.Operations['notnull'] = Element
        self.Add_Keywords('notnull')
        self.Operations['not null'] = Element
        self.Add_Keywords('not null')
        Element = Operation_Number()
        self.Elements.extend([Element])
        self.Operations['number'] = Element
        self.Add_Keywords('number')
        Element = Operation_Or()
        self.Elements.extend([Element])
        self.Operations['or'] = Element
        self.Add_Keywords('or')
        self.Operations['|'] = Element
        self.Add_Keywords('|')
        Element = Operation_Pop()
        self.Elements.extend([Element])
        self.Operations['pop'] = Element
        self.Add_Keywords('pop')
        Element = Operation_Python_Add()
        self.Elements.extend([Element])
        self.Operations['py +'] = Element
        self.Add_Keywords('py +')
        Element = Operation_Python_And()
        self.Elements.extend([Element])
        self.Operations['py and'] = Element
        self.Add_Keywords('py and')
        Element = Operation_Python_Dict_Literal()
        self.Elements.extend([Element])
        self.Operations['py dict'] = Element
        self.Add_Keywords('py dict')
        Element = Operation_Python_Div()
        self.Elements.extend([Element])
        self.Operations['py /'] = Element
        self.Add_Keywords('py /')
        Element = Operation_Python_Eq()
        self.Elements.extend([Element])
        self.Operations['py ='] = Element
        self.Add_Keywords('py =')
        self.Operations['py =='] = Element
        self.Add_Keywords('py ==')
        self.Operations['py = ='] = Element
        self.Add_Keywords('py = =')
        Element = Operation_Python_Fstr()
        self.Elements.extend([Element])
        self.Operations['py fstr'] = Element
        self.Add_Keywords('py fstr')
        Element = Operation_Python_In()
        self.Elements.extend([Element])
        self.Operations['py in'] = Element
        self.Add_Keywords('py in')
        Element = Operation_Python_Is()
        self.Elements.extend([Element])
        self.Operations['py is'] = Element
        self.Add_Keywords('py is')
        Element = Operation_Python_Is_Not()
        self.Elements.extend([Element])
        self.Operations['py is not'] = Element
        self.Add_Keywords('py is not')
        Element = Operation_Python_Isa()
        self.Elements.extend([Element])
        self.Operations['py isa'] = Element
        self.Add_Keywords('py isa')
        Element = Operation_Python_Len()
        self.Elements.extend([Element])
        self.Operations['py len'] = Element
        self.Add_Keywords('py len')
        Element = Operation_Python_List_Literal()
        self.Elements.extend([Element])
        self.Operations['py list'] = Element
        self.Add_Keywords('py list')
        Element = Operation_Python_Ge()
        self.Elements.extend([Element])
        self.Operations['py >='] = Element
        self.Add_Keywords('py >=')
        self.Operations['py > ='] = Element
        self.Add_Keywords('py > =')
        Element = Operation_Python_Gt()
        self.Elements.extend([Element])
        self.Operations['py >'] = Element
        self.Add_Keywords('py >')
        Element = Operation_Python_Le()
        self.Elements.extend([Element])
        self.Operations['py <='] = Element
        self.Add_Keywords('py <=')
        self.Operations['py < ='] = Element
        self.Add_Keywords('py < =')
        Element = Operation_Python_Lt()
        self.Elements.extend([Element])
        self.Operations['py <'] = Element
        self.Add_Keywords('py <')
        Element = Operation_Python_Mod()
        self.Elements.extend([Element])
        self.Operations['py mod'] = Element
        self.Add_Keywords('py mod')
        Element = Operation_Python_Mul()
        self.Elements.extend([Element])
        self.Operations['py *'] = Element
        self.Add_Keywords('py *')
        Element = Operation_Python_Ne()
        self.Elements.extend([Element])
        self.Operations['py !='] = Element
        self.Add_Keywords('py !=')
        self.Operations['py ! ='] = Element
        self.Add_Keywords('py ! =')
        Element = Operation_Python_Neg()
        self.Elements.extend([Element])
        self.Operations['py neg'] = Element
        self.Add_Keywords('py neg')
        Element = Operation_Python_Not()
        self.Elements.extend([Element])
        self.Operations['py not'] = Element
        self.Add_Keywords('py not')
        Element = Operation_Python_Or()
        self.Elements.extend([Element])
        self.Operations['py or'] = Element
        self.Add_Keywords('py or')
        Element = Operation_Python_Slice()
        self.Elements.extend([Element])
        self.Operations['py slice'] = Element
        self.Add_Keywords('py slice')
        Element = Operation_Python_Str()
        self.Elements.extend([Element])
        self.Operations['py str'] = Element
        self.Add_Keywords('py str')
        Element = Operation_Python_Sub()
        self.Elements.extend([Element])
        self.Operations['py -'] = Element
        self.Add_Keywords('py -')
        Element = Operation_Python_Subscript()
        self.Elements.extend([Element])
        self.Operations['py sub'] = Element
        self.Add_Keywords('py sub')
        Element = Operation_Python_Tuple_Literal()
        self.Elements.extend([Element])
        self.Operations['py tuple'] = Element
        self.Add_Keywords('py tuple')
        Element = Operation_Shift()
        self.Elements.extend([Element])
        self.Operations['shift'] = Element
        self.Add_Keywords('shift')
        Element = Operation_Split()
        self.Elements.extend([Element])
        self.Operations['split'] = Element
        self.Add_Keywords('split')
        Element = Operation_String()
        self.Elements.extend([Element])
        self.Operations['string'] = Element
        self.Add_Keywords('string')
        Element = Operation_String_Equal()
        self.Elements.extend([Element])
        self.Operations['s='] = Element
        self.Add_Keywords('s=')
        self.Operations['seq'] = Element
        self.Add_Keywords('seq')
        self.Operations['s ='] = Element
        self.Add_Keywords('s =')
        Element = Operation_String_Greater()
        self.Elements.extend([Element])
        self.Operations['s>'] = Element
        self.Add_Keywords('s>')
        self.Operations['sgt'] = Element
        self.Add_Keywords('sgt')
        self.Operations['s >'] = Element
        self.Add_Keywords('s >')
        Element = Operation_String_Greater_Equal()
        self.Elements.extend([Element])
        self.Operations['s>='] = Element
        self.Add_Keywords('s>=')
        self.Operations['sge'] = Element
        self.Add_Keywords('sge')
        Element = Operation_String_Less()
        self.Elements.extend([Element])
        self.Operations['s<'] = Element
        self.Add_Keywords('s<')
        self.Operations['slt'] = Element
        self.Add_Keywords('slt')
        self.Operations['s <'] = Element
        self.Add_Keywords('s <')
        Element = Operation_String_Less_Equal()
        self.Elements.extend([Element])
        self.Operations['s<='] = Element
        self.Add_Keywords('s<=')
        self.Operations['s <='] = Element
        self.Add_Keywords('s <=')
        self.Operations['s < ='] = Element
        self.Add_Keywords('s < =')
        self.Operations['sle'] = Element
        self.Add_Keywords('sle')
        Element = Operation_String_Not_Equal()
        self.Elements.extend([Element])
        self.Operations['s!='] = Element
        self.Add_Keywords('s!=')
        self.Operations['sne'] = Element
        self.Add_Keywords('sne')
        self.Operations['s !='] = Element
        self.Add_Keywords('s !=')
        self.Operations['s ! ='] = Element
        self.Add_Keywords('s ! =')
        Element = Operation_Substring()
        self.Elements.extend([Element])
        self.Operations['substring'] = Element
        self.Add_Keywords('substring')
        self.Operations['substr'] = Element
        self.Add_Keywords('substr')
        Element = Syntax_Class()
        self.Elements.extend([Element])
        self.Syntaxes['class'] = Element
        self.Add_Keywords('class')
        Element = Syntax_Class_Name()
        self.Elements.extend([Element])
        self.Syntaxes['class name'] = Element
        self.Add_Keywords('class name')
        Element = Syntax_Colon()
        self.Elements.extend([Element])
        self.Syntaxes[':'] = Element
        self.Add_Keywords(':')
        Element = Syntax_Dictionary()
        self.Elements.extend([Element])
        self.Syntaxes['dict'] = Element
        self.Add_Keywords('dict')
        self.Syntaxes['dictionary'] = Element
        self.Add_Keywords('dictionary')
        Element = Syntax_Exclude()
        self.Elements.extend([Element])
        self.Syntaxes['exclude'] = Element
        self.Add_Keywords('exclude')
        Element = Syntax_False()
        self.Elements.extend([Element])
        self.Syntaxes['false'] = Element
        self.Add_Keywords('false')
        Element = Syntax_Flag()
        self.Elements.extend([Element])
        self.Syntaxes['flag'] = Element
        self.Add_Keywords('flag')
        self.Syntaxes['bool'] = Element
        self.Add_Keywords('bool')
        self.Syntaxes['boolean'] = Element
        self.Add_Keywords('boolean')
        Element = Syntax_Indent()
        self.Elements.extend([Element])
        self.Syntaxes['indent'] = Element
        self.Add_Keywords('indent')
        Element = Syntax_Integer()
        self.Elements.extend([Element])
        self.Syntaxes['integer'] = Element
        self.Add_Keywords('integer')
        self.Syntaxes['int'] = Element
        self.Add_Keywords('int')
        Element = Syntax_Is()
        self.Elements.extend([Element])
        self.Syntaxes['is'] = Element
        self.Add_Keywords('is')
        self.Syntaxes['extends'] = Element
        self.Add_Keywords('extends')
        Element = Syntax_Line()
        self.Elements.extend([Element])
        self.Syntaxes['line'] = Element
        self.Add_Keywords('line')
        Element = Syntax_List()
        self.Elements.extend([Element])
        self.Syntaxes['list'] = Element
        self.Add_Keywords('list')
        Element = Syntax_My()
        self.Elements.extend([Element])
        self.Syntaxes['my'] = Element
        self.Add_Keywords('my')
        Element = Syntax_My_Class()
        self.Elements.extend([Element])
        self.Syntaxes['my class'] = Element
        self.Add_Keywords('my class')
        Element = Syntax_Null()
        self.Elements.extend([Element])
        self.Syntaxes['null'] = Element
        self.Add_Keywords('null')
        Element = Syntax_Number()
        self.Elements.extend([Element])
        self.Syntaxes['number'] = Element
        self.Add_Keywords('number')
        Element = Syntax_Object()
        self.Elements.extend([Element])
        self.Syntaxes['object'] = Element
        self.Add_Keywords('object')
        Element = Syntax_Optional()
        self.Elements.extend([Element])
        self.Syntaxes['optional'] = Element
        self.Add_Keywords('optional')
        Element = Syntax_Optrep()
        self.Elements.extend([Element])
        self.Syntaxes['optrep'] = Element
        self.Add_Keywords('optrep')
        self.Syntaxes['optional repeating'] = Element
        self.Add_Keywords('optional repeating')
        Element = Syntax_Our()
        self.Elements.extend([Element])
        self.Syntaxes['our'] = Element
        self.Add_Keywords('our')
        Element = Syntax_Property()
        self.Elements.extend([Element])
        self.Syntaxes['.'] = Element
        self.Add_Keywords('.')
        self.Syntaxes['. .'] = Element
        self.Add_Keywords('. .')
        self.Syntaxes['. . .'] = Element
        self.Add_Keywords('. . .')
        self.Syntaxes['. . . .'] = Element
        self.Add_Keywords('. . . .')
        Element = Syntax_Repeating()
        self.Elements.extend([Element])
        self.Syntaxes['repeating'] = Element
        self.Add_Keywords('repeating')
        Element = Syntax_Return()
        self.Elements.extend([Element])
        self.Syntaxes['return'] = Element
        self.Add_Keywords('return')
        Element = Syntax_Self()
        self.Elements.extend([Element])
        self.Syntaxes['self'] = Element
        self.Add_Keywords('self')
        self.Syntaxes['me'] = Element
        self.Add_Keywords('me')
        Element = Syntax_Sequence()
        self.Elements.extend([Element])
        self.Syntaxes['sequence'] = Element
        self.Add_Keywords('sequence')
        Element = Syntax_String()
        self.Elements.extend([Element])
        self.Syntaxes['string'] = Element
        self.Add_Keywords('string')
        Element = Syntax_Tab()
        self.Elements.extend([Element])
        self.Syntaxes['tab'] = Element
        self.Add_Keywords('tab')
        Element = Syntax_True()
        self.Elements.extend([Element])
        self.Syntaxes['true'] = Element
        self.Add_Keywords('true')
        Element = Syntax_Us()
        self.Elements.extend([Element])
        self.Syntaxes['us'] = Element
        self.Add_Keywords('us')
        Element = Syntax_Variant()
        self.Elements.extend([Element])
        self.Syntaxes['variant'] = Element
        self.Add_Keywords('variant')
        return True

# start of attributes inference
# inference Attributes
# END inference Attributes
# end of attributes inference
# structure inference starts here
# inference Structure
# END inference Structure
# structure inference ends here
# *************************************************************************************
# * data type inference: definitional and contextual types for every language element *
# *************************************************************************************
# 
# Ported from gal2’s Data_Types.gal and extended, per the design note in
# docs/data_type_inference.md. Every element can carry two properties:
# 
# Data_Type is definitional - what the element is. A quote token is a
# string, an addition is a number, a variable is whatever its declaration
# says. Usage is contextual - what the surrounding element applies to it:
# every argument of a say statement is used as a string, the condition of
# an if is used as a flag. When the two differ, a strongly typed generator
# converts; gal itself does not enforce agreement, so a mismatch is the
# generator’s decision, not an error.
# 
# Result types are declarative wherever possible: the dialect declarations
# carry a Data_Type property (the Syntax_True pattern, the same mechanism
# that carries operator precedence), so an operation’s instances default to
# their result type without a handler here. Contextual usage is also mostly
# declarative: the argument declarations in the dialect already state the
# type each statement imposes on each argument, and Declared_Usage below
# stamps those expectations onto the actual arguments through the class
# registry. Handlers are only written where something is not declarable:
# variadic argument lists, declaration statements typing their names, and
# literal tokens.
# 
# Variable references resolve through the contexts Infer_Variables
# populates: declarations and parameters register their names and types in
# the enclosing variable context (the Get_Module pattern - an element asks
# its parent, and scoping elements such as methods return themselves), and
# word tokens look themselves up through that chain.
# 
# inference Data_Types
# variadic statements: every argument is used as a string
# declaration statements type their names definitionally
# ported from the gal2 inference
# END inference Data_Types
# start of inheritance inference
# ***********************************************************************
# * inheritance inference: compile-time flattening of class hierarchies *
# ***********************************************************************
# 
# Ported from gal2 (Inherit in gal2/src/Language.gal, driver in
# Intelligence.gal), per docs/mumps_design.md. Every class statement gains
# Compiled_* member tables with inheritance already applied: ancestor
# tables merge first, own members last, so overrides resolve during the
# merge and a generator never needs to walk a hierarchy. The flattening
# serves targets without a compatible inheritance model (MUMPS routines,
# C) and gives typed backends precomputed member tables.
# 
# The pass fills the Infer_Inheritance stage that has waited in the
# compiler pipeline as a stub, and is behavior-neutral until a generator
# consumes the tables. By the time it runs, class sets have merged into
# their primary classes (Appended_Statements, during Infer_Appends) and
# every class is registered by name in the Statement_Class Names registry
# (during Infer_Attributes), so declaration order never matters.
# 
# Dialect-declared classes (statement, operation, syntax declarations)
# register in the same Names registry but carry no Ancestor property, so
# they flatten as roots for now; extend Inheritance_Name and the ancestor
# probe when a consumer needs their generated ancestry flattened too.
# 
# inference Inheritance
# END inference Inheritance
# end of inheritance inference
# **************************************
# * gal simple syntax parser generator *
# **************************************
class Gal_Token_Parser(Parser):
    def Parse_Character(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Character):
            Top_Token.Error = 'Expected Character'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Char_Number(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Char_Number):
            Top_Token.Error = 'Expected Char_Number'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Char_Punct(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Char_Punct):
            Top_Token.Error = 'Expected Char_Punct'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Char_Line(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Char_Line):
            Top_Token.Error = 'Expected Char_Line'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Char_Ident(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Char_Ident):
            Top_Token.Error = 'Expected Char_Ident'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Token(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Token'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Token_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Token_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Token_Rule(self, Parent_Elements):
        # either Token Token_Line Token_Ws Token_Quote Token_Number Token_Punct Token_Comma Token_Word Character;
        # 
        if self.Parse_Token_Line(Parent_Elements): return True
        if self.Parse_Token_Ws(Parent_Elements): return True
        if self.Parse_Token_Quote(Parent_Elements): return True
        if self.Parse_Token_Number(Parent_Elements): return True
        if self.Parse_Token_Punct(Parent_Elements): return True
        if self.Parse_Token_Comma(Parent_Elements): return True
        if self.Parse_Token_Word(Parent_Elements): return True
        if self.Parse_Character(Parent_Elements): return True
        return False
    def Parse_Token_Comma(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Token_Comma'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Token_Comma_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Token_Comma_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Token_Comma_Rule(self, Parent_Elements):
        # sequence Token_Comma Character_Comma;
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Character_Comma(My_Elements):
            self.Rollback(Start_Char, Start_Token, 'Token_Comma expected Character_Comma.')
            return False
        End = self.Char_Pos
        Element = Token_Comma()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Token_Number(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Token_Number'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Token_Number_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Token_Number_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Token_Number_Rule(self, Parent_Elements):
        # sequence Token_Number [optional ’-’] [repeating Char_Number] [optional ”.”] [optrep Char_Number];
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        # optional ’-’
        self.Parse_Token(My_Elements, '-')
        # repeating Char_Number
        if not self.Parse_Char_Number(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Char_Number] expected at least one Char_Number.')
            return False
        while True:
            if not self.Parse_Char_Number(My_Elements):
                break
        # optional ’.’
        self.Parse_Token(My_Elements, '.')
        # [optrep Char_Number];
        while True:
            if not self.Parse_Char_Number(My_Elements):
                break
        End = self.Char_Pos
        Element = Token_Number()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Token_Punct(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Token_Punct'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Token_Punct_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Token_Punct_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Token_Punct_Rule(self, Parent_Elements):
        # sequence Token_Punct Char_Punct;
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Char_Punct(My_Elements):
            self.Rollback(Start_Char, Start_Token, 'Token_Punct expected Char_Punct.')
            return False
        End = self.Char_Pos
        Element = Token_Punct()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Token_Line(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Token_Line'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Token_Line_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Token_Line_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Token_Line_Rule(self, Parent_Elements):
        # sequence Token_Line Char_Line;
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Char_Line(My_Elements):
            self.Rollback(Start_Char, Start_Token, 'Token_Line expected Char_Line.')
            return False
        End = self.Char_Pos
        Element = Token_Line()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Token_Ws(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Token_Ws'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Token_Ws_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Token_Ws_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Token_Ws_Rule(self, Parent_Elements):
        # sequence Token_Ws [repeating Ws];
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        # repeating Ws
        if not self.Parse_Ws(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Ws] expected at least one Ws.')
            return False
        while True:
            if not self.Parse_Ws(My_Elements):
                break
        End = self.Char_Pos
        Element = Token_Ws()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Ws(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Ws'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Ws_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Ws_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Ws_Rule(self, Parent_Elements):
        # either Ws ’ ’ [tab] Token_Line;
        # 
        if self.Parse_Token(Parent_Elements, ' '): return True
        if True: return '\t'
        return False
    def Parse_Token_Word(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Token_Word'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Token_Word_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Token_Word_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Token_Word_Rule(self, Parent_Elements):
        # sequence Token_Word [repeating Char_Ident];
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        # repeating Char_Ident
        if not self.Parse_Char_Ident(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Char_Ident] expected at least one Char_Ident.')
            return False
        while True:
            if not self.Parse_Char_Ident(My_Elements):
                break
        End = self.Char_Pos
        Element = Token_Word()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True

class Gal_Parser(Parser):
    def Parse_Token_Number(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Token_Number):
            Top_Token.Error = 'Expected Token_Number'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Token_Quote(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Token_Quote):
            Top_Token.Error = 'Expected Token_Quote'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Token_Comma(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Token_Comma):
            Top_Token.Error = 'Expected Token_Comma'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Token_Keyword(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Token_Keyword):
            Top_Token.Error = 'Expected Token_Keyword'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Token_Word(self, Parent_Elements):
        Top_Token = self.Top_Token()
        if (Top_Token in (None, "")): return False
        if not isinstance(Top_Token, Token_Word):
            Top_Token.Error = 'Expected Token_Word'
            return False
        Parent_Elements.extend([Top_Token])
        Top_Token.Error = None
        self.Consume_Token()
        return True
    def Parse_Program(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Program'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Program_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Program_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Program_Rule(self, Parent_Elements):
        # sequence Program [repeating Statement];
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        # repeating Statement
        if not self.Parse_Statement(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Statement] expected at least one Statement.')
            return False
        while True:
            if not self.Parse_Statement(My_Elements):
                break
        End = self.Char_Pos
        Element = Program()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Statement(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Statement'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Statement_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Statement_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Statement_Rule(self, Parent_Elements):
        # sequence Statement [repeating Expression] [optrep Statement_Tail] Statement_End;
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        # repeating Expression
        if not self.Parse_Expression(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Expression] expected at least one Expression.')
            return False
        while True:
            if not self.Parse_Expression(My_Elements):
                break
        # [optrep Statement_Tail] 
        while True:
            if not self.Parse_Statement_Tail(My_Elements):
                break
        if not self.Parse_Statement_End(My_Elements):
            self.Rollback(Start_Char, Start_Token, 'Statement expected Statement_End.')
            return False
        End = self.Char_Pos
        Element = Statement()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Expression(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Expression'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Expression_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Expression_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Expression_Rule(self, Parent_Elements):
        # either Expression Operation Syntax Token_Number Token_Quote Token_Keyword Token_Word;
        # 
        if self.Parse_Operation(Parent_Elements): return True
        if self.Parse_Syntax(Parent_Elements): return True
        if self.Parse_Token_Number(Parent_Elements): return True
        if self.Parse_Token_Quote(Parent_Elements): return True
        if self.Parse_Token_Keyword(Parent_Elements): return True
        if self.Parse_Token_Word(Parent_Elements): return True
        return False
    def Parse_Statement_End(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Statement_End'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Statement_End_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Statement_End_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Statement_End_Rule(self, Parent_Elements):
        # either Statement_End ”;” Block;
        # 
        if self.Parse_Token(Parent_Elements, ';'): return True
        if self.Parse_Block(Parent_Elements): return True
        return False
    def Parse_Block(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Block'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Block_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Block_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Block_Rule(self, Parent_Elements):
        # sequence Block ”{” [optrep Statement] ”}”;
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Token(My_Elements, '{'):
            self.Rollback(Start_Char, Start_Token, f'Block expected {{.')
            return False
        # [optrep Statement] 
        while True:
            if not self.Parse_Statement(My_Elements):
                break
        if not self.Parse_Token(My_Elements, '}'):
            self.Rollback(Start_Char, Start_Token, f'Block expected }}.')
            return False
        End = self.Char_Pos
        Element = Block()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Operation(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Operation'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Operation_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Operation_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Operation_Rule(self, Parent_Elements):
        # sequence Operation ’(’ [repeating Expression] ’)’;
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Token(My_Elements, '('):
            self.Rollback(Start_Char, Start_Token, f'Operation expected (.')
            return False
        # repeating Expression
        if not self.Parse_Expression(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Expression] expected at least one Expression.')
            return False
        while True:
            if not self.Parse_Expression(My_Elements):
                break
        if not self.Parse_Token(My_Elements, ')'):
            self.Rollback(Start_Char, Start_Token, f'Operation expected ).')
            return False
        End = self.Char_Pos
        Element = Operation()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Syntax(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Syntax'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Syntax_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Syntax_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Syntax_Rule(self, Parent_Elements):
        # sequence Syntax ’[’ [repeating Expression] [optrep Syntax_Tail] ’]’;
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Token(My_Elements, '['):
            self.Rollback(Start_Char, Start_Token, f'Syntax expected [.')
            return False
        # repeating Expression
        if not self.Parse_Expression(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Expression] expected at least one Expression.')
            return False
        while True:
            if not self.Parse_Expression(My_Elements):
                break
        # [optrep Syntax_Tail] 
        while True:
            if not self.Parse_Syntax_Tail(My_Elements):
                break
        if not self.Parse_Token(My_Elements, ']'):
            self.Rollback(Start_Char, Start_Token, f'Syntax expected ].')
            return False
        End = self.Char_Pos
        Element = Syntax()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Syntax_Tail(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Syntax_Tail'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Syntax_Tail_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Syntax_Tail_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Syntax_Tail_Rule(self, Parent_Elements):
        # sequence Syntax_Tail ’,’ [repeating Expression];
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Token(My_Elements, ','):
            self.Rollback(Start_Char, Start_Token, f'Syntax_Tail expected ,.')
            return False
        # repeating Expression
        if not self.Parse_Expression(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Expression] expected at least one Expression.')
            return False
        while True:
            if not self.Parse_Expression(My_Elements):
                break
        End = self.Char_Pos
        Element = Syntax_Tail()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True
    def Parse_Statement_Tail(self, Parent_Elements):
        Memo_Key = f'{ str(self.Token_Pos) }:Statement_Tail'
        Memo_Hit = self.Memo_Get(Memo_Key)
        if not (Memo_Hit in (None, "")):
            return self.Memo_Replay(Memo_Hit, Parent_Elements)
        Memo_Start_Token = self.Token_Pos
        Memo_Start_Char = self.Char_Pos
        Memo_Seed = self.Memo_Plant(Memo_Key)
        Memo_Produced = []
        Memo_Result = self.Parse_Statement_Tail_Rule(Memo_Produced)
        self.Memo_Settle(Memo_Seed, Memo_Result, Memo_Produced)
        if Memo_Seed.Detected and Memo_Result:
            while True:
                self.Memo_Regrow_Begin(Memo_Seed)
                self.Token_Pos = Memo_Start_Token
                self.Char_Pos = Memo_Start_Char
                Memo_Grow = []
                Memo_Grow_Result = self.Parse_Statement_Tail_Rule(Memo_Grow)
                if not self.Memo_Grew(Memo_Seed, Memo_Grow_Result, Memo_Grow):
                    break
        self.Memo_Finish(Memo_Seed)
        return self.Memo_Replay(Memo_Seed, Parent_Elements)
    def Parse_Statement_Tail_Rule(self, Parent_Elements):
        # sequence Statement_Tail ’,’ [repeating Expression];
        # 
        Start_Char = self.Char_Pos
        Start_Token = self.Token_Pos
        My_Elements = []
        if not self.Parse_Token(My_Elements, ','):
            self.Rollback(Start_Char, Start_Token, f'Statement_Tail expected ,.')
            return False
        # repeating Expression
        if not self.Parse_Expression(My_Elements):
            self.Rollback(Start_Char, Start_Token, '[repeating Expression] expected at least one Expression.')
            return False
        while True:
            if not self.Parse_Expression(My_Elements):
                break
        End = self.Char_Pos
        Element = Statement_Tail()
        First_Child = self.Tokens[Start_Token]
        Start_Char = First_Child.Start_Position
        Element.Start_Position = Start_Char
        Element.End_Position = End
        Element.Document = self
        Element.Elements = My_Elements.copy()
        self.Add_Element(Element)
        Parent_Elements.extend([Element])
        return True

class Gal_Generator(Generator):
    def __init__(self, Owner=None):
        super().__init__()
        self.Verbosity = False # flag
        self.Language_Name = 'Gal' # string
        self.Property_Name = 'Gal' # string
        self.Owner = Owner
    def Infer_Gal(self):
        # this verbosity defined in gal3 fallback_inference.txt for Statement_Generator.
        Verbose = self.Verbosity
        Elem = None
        I = None
        Number = -1
        Error = None
        self.Status = True
        for Elem in self.Elements:
            try:
                (Number) += 1
                if Elem.Classification is not None:
                    I = Elem.Classification
                    I.Infer_Gal()
                    Elem.Gal = I.Gal
                else:
                    Elem.Infer_Gal()
            except Exception as Error:
                self.Status = False
                Elem.Error = Error
                if Verbose:
                    print(f'!error! Gal element { Number }: { I.__class__.__name__ }, <{ Error }>')
        if not self.Status: return False
        Top = self.Elements[-1]
        Top.Infer_Gal()
        Code = str(Top.Gal)
        self.Gal = Code
        self.Code = Code
        return True

# ENGLISH: generate the optimal gal code for each language element in the compiler dialect.
# include resolution: replace the statement with the text of the
#     named plugin’s compiled .gal file. only the gal stage resolves includes,
#     and only .gal files (which are include-free by construction) can be
#     included, so nested includes terminate at build time instead of
#     recursing here.
class Gal_Compiler(Compiler):
    def __init__(self):
        super().__init__()
        self.Token_Parser = Gal_Token_Parser() # object
        self.Parser = Gal_Parser() # object
        self.Generator = Gal_Generator(self) # object
        self.Dialect = Dialect_Compiler() # object
    def Element_Report(self):
        Text = ''
        Elem = None
        Count = 0
        for Elem in self.Elements:
            Text += f'{ str(Count) }. { Elem.__class__.__name__ }'
            if isinstance(Elem, Spell):
                Text += f'/{ Elem.Classification.__class__.__name__ } args { str(len(Elem.Arguments)) } largs { str(len(Elem.Listargs)) } kw { str(len(Elem.Keywords)) }'
            try:
                if not (Elem.Gal in (None, "")):
                    Text += f' gal <{ Elem.Gal }>'
            except Exception: pass
            try:
                if not (Elem.Fallback in (None, "")):
                    Text += f' fallback <{ Elem.Fallback }>'
            except Exception: pass
            try:
                if not (Elem.Python in (None, "")):
                    Text += f' python <{ Elem.Python }>'
            except Exception: pass
            try:
                if not (Elem.Javascript in (None, "")):
                    Text += f' javascript <{ Elem.Javascript }>'
            except Exception: pass
            try:
                if not (Elem.Error in (None, "")):
                    Text += f' ERROR <{ Elem.Error }>'
            except Exception: pass
            Text += str('\n')
            (Count) += 1
        return Text
    def Infer_Tokens(self):
        # the gal parser never sees whitespace: scan with the string
        #         lexer and drop whitespace and line tokens
        return self.Scan_Tokens(False)
    def Infer_Code(self):
        Verbose = False
        if Verbose:
            print('Gal_Compiler.Infer_Code: starting code generation')
        self.Generator.Elements = self.Elements
        self.Generator.Infer_Gal()
        if Verbose:
            print('Gal_Compiler.Infer_Code: calling Generator.Infer_Gal')
        # a failed include must abort the build: the generator loop
        #         records the failure on the element, and without this check a
        #         silently truncated program would be written as if it succeeded.
        Elem = None
        for Elem in self.Elements:
            if not isinstance(Elem, Spell):
                continue
            try:
                if isinstance(Elem.Classification, Statement_Include) and not (Elem.Error in (None, "")):
                    print(f'gal include failed: { Elem.Error }')
                    return 0
            except Exception: pass
        # Get the top-level program element
        Top = self.Elements[-1]
        if Verbose:
            Report = str(self.Element_Report())
            print(Report)
        if Verbose:
            print('Gal_Compiler.Infer_Code: ensuring Top element has gal code')
        try:
            if Top.Gal is None:
                raise ValueError
        except (ValueError, AttributeError):
            print(str(self.Error_Report()))
            return 0
        Code = str(Top.Gal)
        self.Gal = Code
        if Verbose:
            print('Gal_Compiler.Infer_Code: successfully generated gal code')
        return 1

# ****************************************************************************************************************
# * fallback inference, generates simpler gal code, allowing highly abstract language elements to be implemented in concrete programming languages. *
# ****************************************************************************************************************
class Fallback_Generator(Gal_Generator):
    def __init__(self, Owner=None):
        super().__init__()
        self.Verbosity = False # flag
        self.Language_Name = 'Fallback' # string
        self.Property_Name = 'Fallback' # string
        self.Owner = Owner
    def Infer_Fallback(self):
        # this verbosity defined in gal3 fallback_inference.txt for Statement_Generator.
        Verbose = self.Verbosity
        Elem = None
        I = None
        Number = -1
        Error = None
        self.Status = True
        for Elem in self.Elements:
            try:
                (Number) += 1
                if Elem.Classification is not None:
                    I = Elem.Classification
                    I.Infer_Fallback()
                    Elem.Fallback = I.Fallback
                else:
                    Elem.Infer_Fallback()
            except Exception as Error:
                self.Status = False
                Elem.Error = Error
                if Verbose:
                    print(f'!error! Fallback element { Number }: { I.__class__.__name__ }, <{ Error }>')
        if not self.Status: return False
        Top = self.Elements[-1]
        Top.Infer_Fallback()
        Code = str(Top.Fallback)
        self.Fallback = Code
        self.Code = Code
        return True

# ENGLISH: generate the optimal fallback code for each language element in the compiler dialect.
# include statements are resolved by the gal stage; a file that
#     still contains one when it reaches fallback was not produced by the gal
#     compiler. fail loudly instead of passing it downstream.
# python-specific elements lower to gal atomics here. these are
#     the equivalency point between python semantics and gal semantics: a
#     future target language that disagrees with the lowering overrides these
#     same classes instead of touching the python-to-gal translator.
# TODO: add more class handlers above this line
class Fallback_Compiler(Gal_Compiler):
    def __init__(self):
        super().__init__()
        self.Generator = Fallback_Generator(self)
    def Infer_Code(self):
        Verbose = False
        if Verbose:
            print('Fallback_Compiler.Infer_Code: starting code generation')
        self.Generator.Elements = self.Elements
        self.Generator.Infer_Gal()
        self.Generator.Verbosity = True
        Status = self.Generator.Infer_Fallback()
        if Status == 0: return Status
        if Verbose:
            print('Fallback_Compiler.Infer_Code: calling Generator.Infer_Fallback')
        # Call Infer_Fallback to generate the code
        self.Generator.Infer_Fallback()
        # Get the top-level program element
        Top = self.Elements[-1]
        if Verbose:
            print('Fallback_Compiler.Infer_Code: ensuring Top element has fallback code')
        try:
            if Top.Fallback is None:
                raise ValueError
        except (ValueError, AttributeError):
            print(str(self.Error_Report()))
            return 0
        Code = str(Top.Fallback)
        self.Fallback = Code
        if Verbose:
            print('Fallback_Compiler.Infer_Code: successfully generated fallback code')
        return 1

# ************************
# * gal to fallback main *
# ************************
if __name__ == '__main__':
    try:
        Source_File = sys.argv[1]
        Target_File = sys.argv[2]
    except:
        print("Usage: ", sys.argv[0], "Source_File Target_File")
        sys.exit()
    Verbose = False
    if Verbose:
        print('fallback3 compiler')
    if Verbose:
        print(f'input file: { Source_File }')
    Report_File = f'{ Target_File }.elems'
    FC = Fallback_Compiler()
    FC.Initialize()
    FC.File_Name = Source_File
    FC.Code = '<undefined>'
    Result = FC.Infer()
    Unclassified = str(FC.Dialect.Print_Unclassified_Verbs())
    if Unclassified > '':
        print(Unclassified)
    if Result > 0:
        with open(Target_File, 'w', encoding='utf-8') as _file:
            _file.write(FC.Fallback)
    else:
        with open(Report_File, 'w', encoding='utf-8') as _file:
            _file.write(FC.Element_Report())
        if Verbose:
            print(f'wrote { Report_File }')
        print('Fallback Error, output not written')

