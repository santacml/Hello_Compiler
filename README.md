# Hello_Compiler
Compiler for the course EECE6083 at the University of Cincinnati.

# Usage
First, it will be necessary to compile the runtime library for your system. Navigate to the runtime folder and then in a Unix environment:

```
gcc -c -Wall -Werror -fpic runtime.c
gcc -shared -o runtimelib.so runtime.o
```

Next, Python 3 (Python 2 will not work) will need to be installed as well as the library LLVMLite. Install Python 3, then using Pip (or Conda):

```
pip install llvmlite
or
conda install llvmlite
```

Now the compiler is ready to use. Call using:

```
python hello_compiler.py FILE_NAME
```

Where FILE_NAME is the file to be compiled. If no file name is provided, it will default to test.src.

At the moment, the output llvm code is printed to standard output and then immediately run, terminating with EXIT: 0.
