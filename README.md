pykit
=====

Backend compiler for high-level typed code with first-class support for
multi-dimensional arrays, list tuples and dicts. High-level operations
are optimized and must be lowered to a runtime implementation. Provided
runtime implementations are in place for memory management and garbage
collection, exceptions and threads.

You can think of pykit as an easier to use layer on-top of llvmpy. Easier
to understand errors, and generally more developer friendly.

Pykit tries to address an ever-growing number of compilers in the Python
community, with a focus on array-oriented numerical code.

pykit:

    * lowers and optimizes intermediate code
    * produces IR that can be mapped to any desired runtime
    * tries to be independent from platform or high-level language
    * can generate LLVM or C89 out of the box

pykit is inspired by VMKit and LLVM.

Website
=======
http://pykit.github.io/pykit/

Documentation
=============
http://pykit.github.io/pykit-doc/
