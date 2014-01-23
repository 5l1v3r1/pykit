Pykit IR
========

The pykit IR is a linear N-address code delineated through basic blocks,
analogously to LLVM IR. It defines a set of opcodes, which specify what
an operation does. Opcodes range from high-level such as container operations,
to low-level operations such as pointer stores. Each operation has a type,
and implicit coercions do not exists. Instead coercions need explicit
conversions.

Similarly to LLVM pykit comes with an ``alloca`` instruction that allocates
an object on the stack, such as a scalar or a small array. The resulting
pointer can be loaded and stored to.

Pykit uses SSA, and can promote stack allocated scalars to virtual registers
and remove the load and store operations, allowing better optimizations
since values propagate directly to their use sites.

All opcodes are defined in ``pykit.ir.ops``. Below follows a summary and
rationale.

Control Flow
------------

Control flow is supported through through ``jump``, ``cbranch`` and ``ret``.
Additionally, ``phi`` merges different incoming values or definitions from
predecessor basic blocks.

Exceptions are supported through ``exc_setup``, ``exc_catch`` and
``exc_throw``.

    * ``exc_setup``: marks the exception handlers for the basic block
    * ``exc_catch``: specifies which exceptions this basic block can handle
    * ``exc_throw``: raises an exception

The implementation is pluggable (costful/zero-cost, etc), and these opcodes
are entirely optional. More on this can be read here: :ref:`lowering`.

Attributes
----------

Attributes are supported through ``getfield`` and ``setfield`` for objects
and structs.

Conversion
----------

The ``convert`` opcode converts its argument to the destination type.

Functions
---------

Pykit considers external and defined functions to be functions. These can
be called through the ``call`` opcode. Additionally, pykit supports partial
functions, which are also functions. Only these functions may be passed to
``map`` etc, or used in ``phi`` instructions (if the signatures are compatible).

Math is supported through ``call_math``, since the functions have polymorphic
signatures (real or complex). Math functions take a constant function name as
first argument. These are defined in ``ops.py``.

Note that pykit does not support keyword arguments. A front-end can however
handle this statically if possible, or otherwise rewrite the signature to
take an explicit dictionary as argument if so desired (and star arguments
through an explicit tuple).

Pointers
--------

Supported pointer operations are ``add``, ``ptrload`` and ``ptrstore``.
``ptrcast`` casts the pointer to another pointer (this is distinguished from
a data conversion).
