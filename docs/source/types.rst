Pykit Types
===========

Pykit supports the following types:

    * Functions (as first-class values)
    * Integral and real numbers
    * Structs and Unions
    * Pointers

Additionally, pykit supports the notion of a Typedef, which allows a type to be
declared and used now, but resolved later::

    Int = Typedef("Int", Int32)

Above we specify that an ``Int`` type is *like* an ``Int32``, but we don't
fix this representation. This allows the IR to retain portability to a later
stage (or all the way to e.g. C code).
