#!/usr/bin/env python3
"""
This script adds a main() function to the Runtime.py file in the .gal3 directory.
"""

import os
import sys

# Define the main function to add
MAIN_FUNCTION = """
    @classmethod
    def main(cls, args):
        \"\"\"
        Main entry point for the runtime.
        Args:
            args: List of command line arguments.
                  The first argument should be the compiler file path,
                  The second argument should be the input file to compile.
        \"\"\"
        if len(args) < 1:
            print("Usage: main.py compiler_file.txt [input_file.gal]")
            return 1
        
        compiler_file = args[0]
        input_file = args[1] if len(args) > 1 else "new_file.gal"
        
        # Import necessary modules
        try:
            # Use dynamic import to avoid circular imports
            gal_module = __import__('gal')
            Gal_Compiler = getattr(gal_module, 'Gal_Compiler')
        except ImportError as e:
            print(f"Error importing Gal_Compiler: {e}")
            return 1
        
        # Initialize the compiler
        compiler = Gal_Compiler()
        compiler.Initialize()
        compiler.File_Name = input_file
        compiler.Code = '<undefined>'
        compiler.Infer()
        
        # Print the results
        print(compiler.Element_Report())
        print(f"Generated code: {compiler.Gal}")
        compiler.Dialect.Print_Unclassified_Verbs()
        
        return 0
"""

def add_main_to_runtime():
    """Add the main function to the Runtime.py file in the .gal3 directory."""
    runtime_path = os.path.expanduser("~/.gal3/Runtime.py")
    
    if not os.path.exists(runtime_path):
        print(f"Error: Runtime.py not found at {runtime_path}")
        return 1
    
    # Read the current content
    with open(runtime_path, "r") as f:
        content = f.read()
    
    # Check if main function already exists
    if "def main(cls, args)" in content:
        print("The main function already exists in Runtime.py")
        return 0
    
    # Find the position to insert the main function (right before the last line)
    lines = content.splitlines()
    new_content = lines[:-1]
    new_content.append(MAIN_FUNCTION)
    new_content.append(lines[-1])  # Add the last line back
    
    # Write the updated content
    with open(runtime_path, "w") as f:
        f.write("\n".join(new_content))
    
    print(f"Successfully added main function to {runtime_path}")
    return 0

if __name__ == "__main__":
    sys.exit(add_main_to_runtime())