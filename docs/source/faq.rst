FAQ
===

Why not LLVM IR?
----------------

Why not directly use LLVM IR for the internal format? There are pros and
cons to doing that, below are some reasons why not to:

    * Completeness, we can encode all high-level constructs directly in
      the way we wish, without naming schemes, LLVM metadata, or external
      data
    * Instruction polymorphism the way we want it
    * Control over the types you want to support
    * Pluggable optimizations
    * Simple arbitrary metadata through a key/value mechanism
    * No aborting, ever
