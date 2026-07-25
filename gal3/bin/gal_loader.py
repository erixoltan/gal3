#!/usr/bin/env python3
import os
import sys

# Add the .gal3 directory to the path so we can import Runtime and gal.py
sys.path.append(os.path.expanduser('~/.gal3'))

# Define main function to load and run the gal compiler
def main(argv):
    if len(argv) < 1:
        print("Usage: gal_loader.py file_to_compile.gal")
        return 1
    
    # Import the Runtime class
    from Runtime import Runtime
    
    # Load and process the main compiler file
    file_name = argv[0] if argv else "gal_main.txt"
    input_file = argv[1] if len(argv) > 1 else "new_file.gal"
    
    # Read the compiler source
    compiler_text = Runtime.File_Readall(file_name)
    
    print(f"Loading compiler from {file_name}")
    print(f"Compiling file: {input_file}")
    
    # Create a compiler object
    from gal import Gal_Compiler
    compiler = Gal_Compiler()
    compiler.Initialize()
    compiler.File_Name = input_file
    compiler.Code = '<undefined>'
    compiler.Infer()
    
    # Print results
    print(compiler.Element_Report())
    print(f"Generated code: {compiler.Gal}")
    compiler.Dialect.Print_Unclassified_Verbs()
    
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))