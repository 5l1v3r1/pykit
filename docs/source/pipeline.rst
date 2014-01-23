Pykit pipeline
==============

The input to pykit is a typed program in the form of a Module, consisting of
a set of functions, global variables and external symbols.

The functions within the module go through successive transformations or
stages defined by the pipeline. We can categorize stages as follows
(similar to parakeet):

    * High-level optimizations and analyses
    * Lowering and scalarization
    * Codegen

Every stage in the pipeline is optional. The order is configurable. Entire
stages can be skipped or overridden.

High-level Optimizations and Analyses
-------------------------------------

Transformations and optimizations:

    * SSA/mem2reg

    * Sparse conditional constant propagation
    * Purity analysis
    * Escape analysis
    * Partial redundancy elimination
    * Scalar replacement
    * Inlining
    * Exception analysis

We need to perform these analyses on high-level code, since subsequent
lowering transformations will reduce or preclude the effectiveness.

Codegen
-------

The code is in a low-level format by now, and can be easily used to generate
code from. We are left with:

    * Scalars operations (int, float, pointer, function)
    * Aggregate accesses (struct, union)
    * Scalar conversions and pointer casts
    * Memory operations (load, store)
    * Control flow (branch, conditional branch, return, exceptions)
    * Function calls
    * phi
    * Constants
