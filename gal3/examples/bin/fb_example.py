class Statement_Foo(Scoped_Statement):
    self.Keyword = 'foo' # string
    def Attributes(self):
        if ((llength [my Listargs]) = 0):
            error 'missing required argument One';
        my = One;
        [my One Data_Type] = 'integer';
        [my One Usage] = 'value';
        if ((llength [my Listargs]) = 0):
            error 'missing required argument Two';
        my = Two;
        [my Two Data_Type] = 'string';
        [my Two Usage] = 'value';
        return True
    self.One = None # object
    self.Two = None # object
    def Infer_Example(self):
        # string Code
        my = Example;
class Operation_Bar(Binary_Statement):
    self.Keyword = 'bar' # string
    def Attributes(self):
        if ((llength [my Listargs]) = 0):
            error 'missing required argument Three';
        my = Three;
        [my Three Data_Type] = 'class';
        [my Three Usage] = 'class';
        return True
    self.Three = None # object
    optional Four 'string' 'value';
    def Infer_Example(self):
        # string Code
        my = Example;
class Example_Generator(Generator):
    self.Language_Name = 'Example' # string
    self.Property_Name = 'Example' # string
    constructor [object Owner]
    {
        my = Owner;
    }
    def Infer_Example(self):
        comment 'this verbosity defined in gal3 fallback_inference.txt for Statement_Generator.';
        flag Verbose [false];
        # object Elem
        # object I
        Number = -1
        # variant Error
        my = Status;
        for each Elem in [my Elements]
        {
            try
            {
                + + Number;
                defined [Elem.Classification]
                {
                    I = [Elem.Classification];
                    I.Infer_Example;
                    Elem.Example = [I.Example];
                }
                else
                {
                    Elem.Infer_Example;
                }
            }
            catch Error
            {
                my = Status;
                Elem.Error = Error;
                if Verbose
                {
                    say '!error! Example element ' Number ': ' [I class name] ', <' Error '>, source ' (Elem.Get_Input) ' string  ' (Elem.To_String);
                }
            }
        }
        return [false] if (not [my Status]);
        Top = (llast [my Elements])
        Top.Infer_Example()
        # string Code
        my = Example;
        my = Code;
        return True
