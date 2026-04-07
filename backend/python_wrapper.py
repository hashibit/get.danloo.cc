#!/usr/bin/env python3
import sys
import os

# Add the user site packages to Python path
sys.path.insert(0, '/home/appuser/.local/lib/python3.11/site-packages')

# Execute the command
if len(sys.argv) > 1:
    if sys.argv[1] == '-c':
        # Execute Python code
        exec(sys.argv[2])
    elif sys.argv[1] == '-m':
        # Execute module
        module_name = sys.argv[2]
        import runpy
        runpy.run_module(module_name, run_name="__main__")
    else:
        # Execute command
        os.execvp(sys.argv[1], sys.argv[1:])
else:
    print("Usage: python_wrapper.py <command> [args...]")