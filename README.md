pykit
=====

Pykit is a package for a pluggable intermediate representation, that
is higher level and easier to use than LLVM. It allows pluggable compiler
optimizations and custom opcodes, and aims to abstract over backends
(e.g. C or LLVM), IR serialization and caching, debug information.
exception handling and potentially GC root finding.

Pykit ships with a builtin set of opcodes, and has an IR verifier and
interpreter for that set of operations. The IR is a function of basic
blocks containing instructions (operations), similar to three-address
code. It supports builtin variables and explicit SSA instructions
through the dataflow and reg2mem passes.

Although pykit ships with builtin opcodes and passes, one is entirely
free to use a custom set of opcodes, types and transformations.

pykit:

    * lowers and optimizes intermediate code
    * tries to be independent from platform or high-level language
    * can generate LLVM or C89 out of the box
        - todo: finish C codegen :)
    * supports pluggable opcodes
    * has a number of builtin optimizations and transformations
    * has a builtin set of goodies to work with the IR
        - builder, interpreter, verifier
    * supports float and complex math functions through llvmmath

pykit is inspired by VMKit and LLVM.

Website
=======
http://pykit.github.io/pykit/

Documentation
=============
http://pykit.github.io/pykit-doc/
