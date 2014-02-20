pykit
=====

Pykit is a package for a pluggable intermediate representations, that
is higher level and easier to use than LLVM. You can think of it as a
toolbox of several parts:

    * an IR
    * a number of builtin compiler analyses, transformations and optimizations
    * a C and LLVM code generator
    * a set of builtin opcodes

Pykit ships with a set of builtin opcodes and types for which the compiler
passes and code generator are defined. However, one is entirely free to use
one's own opcodes, or mix higher level opcodes with lower level ones defined
by pykit.

For instance, flypy starts with a higher-level set of opcodes, and uses a
number of passes from pykit while still using a good number of its own opcodes.
For instance, when the IR is still untyped and there are abstract opcodes such
as "retrieve this attribute from this object" is uses the dataflow pass to
translate variable writes and reads into SSA.

In additionl to pluggable opcodes, the optimizations and passes are often
pluggable, for instance the sparse conditional constant propagation pass is
parameterized by a constant folder. The aim is flexibility and abstraction,
i.e. to reduce the burden for new compilers to support multiple backends
(e.g. C or LLVM), to serialize and cache IR, to generate debug information,
exception handling and potentially GC root finding, and so forth.

Pykit also has an IR verifier and interpreter for that set of operations.
The IR is a function of basic blocks containing instructions (operations),
similar to three-address code. One can refer to the arguments as well as
the uses of an instruction.

Although pykit ships with builtin opcodes and passes, one is entirely
free to use a custom set of opcodes, types and transformations.

To summarize, pykit:

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
