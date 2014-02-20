Pykit pipeline
==============

The input to pykit is a typed function inside a Module, which in turn
consists of a set of functions, global variables and external symbols.

The functions within the module go through successive transformations or
stages defined by the pipeline. Pipelines are entirely configurable and
optional. For instance, one may wish to simply use transformations and passes
where suitable from an externally managed pipeline.

Analyses, transformations and Optimizations
-------------------------------------------

Transformations and optimizations:

    * SSA: mem2reg and reg2mem
    * Sparse conditional constant propagation, constant folding
    * Call graph
    * Loop detection
    * Inlining
    * Dead code elimination
    * Exception analysis

These passes may be useful for use from other compilers. For instance, SCCP
on a low-level code isn't necessarily useful since LLVM or a C compiler will
perform that optimization.

However, pykit allows folding of any type of  constant, and it may be useful
to run such optimizations earlier in a pipeline before introducing code
through lowering passes which can not easily (or possibly) be optimized.

Codegen
-------

The input to the code generators is a low-level IR that only contains:

    * Scalars operations (int, float, pointer, function)
    * Aggregate accesses (struct, union)
    * Scalar conversions and pointer casts
    * Memory operations (load, store)
    * Control flow (branch, conditional branch, return, exceptions)
    * Function calls
    * phi
    * Constants
