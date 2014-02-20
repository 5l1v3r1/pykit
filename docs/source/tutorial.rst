Tutorial
========

The central construct in pykit is the intermediate representation, which is
encoded through a number of classes. Opcodes can be chosen from the set of
available pykit opcodes, which can be viewed here:

    https://github.com/pykit/pykit/blob/master/pykit/ir/ops.py#L45

One is free to choice custom opcodes however. In the following example we
will show how to construct and manipulate IR.

Constructing IR
===============

All instructions that form some operation are grouped into a Function.
We can create a function with a name and a signature:

.. code-block:: python

    >>> from pykit.ir import Function
    >>> from pykit import types

    >>> signature = types.Function(restype=types.Float32,
    ...                            argtypes=[types.Float32, types.Float32],
    ...                            varargs=False)
    >>> func = Function("myfunc", ["a", "b"], signature)
    >>> print(func)
    function Float32 myfunc(Float32 %a, Float32 %b) {

    }


Great, we just build an function that does nothing :). We can now start to
populate it with some basic blocks and instructions. Lets make it add these
numbers:

.. code-block:: python

    >>> from pykit.ir import Builder

    >>> # Add a basic block
    >>> entry_block = func.new_block("entry")

    >>> # Get arguments from function
    >>> a, b = func.args
    >>> print(a)
    %a
    >>> print(b)
    %b

    >>> # Construct builder to easily construct instructions (pykit.ir.Op)
    >>> builder = Builder(func)
    >>> # Tell the builder where these instructions should end up
    >>> builder.position_at_beginning(entry_block)

    >>> # Generate instructions
    >>> square = builder.mul(a, b)
    >>> builder.ret(square)

    >>> print(func)
    function Float32 myfunc(Float32 %a, Float32 %b) {
    entry:
        %.0    = mul(%a, %b) -> Float32
        %.1    = ret(%.0) -> Void

    }

In the example above we used the Builder class to emit Ops in our function.
A builder needs to be positioned in order to insert the instructions at the
right place. There are several ways to do that which we explain in the
:ref:`builder` document.

Note also how our `ret` instruction is of type
`Void`, since the operation itself is not an expression and cannot be referred
to. The result of the `mul` instruction is `Float32`, which the Builder
determined from the input types.

Now, we're using pykit's typesystem here, but one is free to use one's own
type system. This can be done by typing everything using `types.Opaque`, or
simply by passing in one's own types.

Passes
======

We can now run existing pykit passes on the IR we constructed, we can compile
the result, or we can transform or add to it as we see fit. Here we will
demonstrate how to write a simple pass to modify the IR. This itself may be
part of a larger pipeline, which is documented in :ref:`pipeline`.

Here we'll attempt to rewrite `exp(x) - 1` to `expm1(x)`. We start by
constructing an example function:

.. code-block:: python

    >>> from pykit.ir import Const

    >>> signature = types.Function(restype=types.Float64,
    ...                            argtypes=[types.Float64],
    ...                            varargs=False)
    >>> func = Function("myfunc", ["x"], signature)
    >>> entry_block = func.new_block("entry")
    >>> builder = Builder(func)
    >>> builder.position_at_beginning(entry_block)
    >>> # Emit instructions
    >>> x = func.args[0]
    >>> exp_x = builder.call_math(types.Float64, "exp", [x])
    >>> sub   = builder.sub(exp_x, Const(1.0, types.Float64))
    >>> builder.ret(sub)

    >>> print(func)
    function Float64 myfunc(Float64 %x) {
    entry:
        %.0    = call_math(exp, [%x]) -> Float64
        %.1    = sub(%.0, const(1.0, Float64)) -> Float64
        %.2    = ret(%.1) -> Void

    }

Now, our goal is to transform the instructions `%0` and `%1` to use the
`expm1` function instead. This involves roughly three steps:

    1. Match the pattern `exp(x) - 1`
    2. Recognize that the rewrite is valid, i.e. that `exp(x)` is used only
       in the expression `exp(x) - 1`
    3. Rewrite the instructions, ensuring that anything referring to the
       expression will now refer to the new result


We will proceed by matching the expression, and looking at the context in which
the result of the `exp(x)` is used by inspecting the `uses`. For instruction
`%0`, the uses is the set `{ %1 }`, which is the only instruction referring
to the result. When these conditions are met, we will delete operation `%0`
and replace `%1` with the new result. Alternatively, we could introduce the
new result, replace the uses of `%1` with the new result, and then delete `%0`
and `%1`.

We write the following pass:

.. code-block:: python

    def rewrite_exp(func):
        for op in func.ops:
            if op.opcode == 'sub':
                arg1, arg2 = op.args
                # 1. Perform the pattern match
                is_exp = arg1.opcode == 'call_math' and arg1.args[0] == 'exp'
                is_one = isinstance(arg2, Const) and arg2.const == 1.0
                # 2. Check the uses
                uses = func.uses[arg1]
                if is_exp and is_one and len(uses) == 1:
                    # 3. Rewrite operations
                    exp_name, [x] = arg1.args

                    # Construct new op with opcode "call_math", result type
                    # Float64, and reuse the register name from the expression
                    # (`op.result`). The arguments are simply the arguments to
                    # the call_math opcode: the name of the math function and
                    # some value (`x`).
                    new_op = Op("call_math", types.Float64, ["expm1", [x]],
                                op.result)

                    # Replace and clean up
                    op.replace(new_op)
                    arg1.delete()


And test it on an example:

.. code-block:: python

    >>> from pykit.ir import Const, Op

    >>> # Build function
    >>> signature = types.Function(restype=types.Float64,
    >>>                            argtypes=[types.Float64],
    >>>                            varargs=False)
    >>> func = Function("myfunc", ["x"], signature)
    >>> entry_block = func.new_block("entry")
    >>> builder = Builder(func)
    >>> builder.position_at_beginning(entry_block)

    >>> # Emit instructions
    >>> x = func.args[0]
    >>> exp_x = builder.call_math(types.Float64, "exp", [x])
    >>> sub   = builder.sub(exp_x, Const(1.0, types.Float64))
    >>> builder.ret(sub)

    >>> print(func)
    function Float64 myfunc(Float64 %x) {
    entry:
        %.0    = call_math(exp, [%x]) -> Float64
        %.1    = sub(%.0, const(1.0, Float64)) -> Float64
        %.2    = ret(%.1) -> Void

    }

    >>> # Test our example!
    >>> rewrite_exp(func)
    >>> print(func)
    function Float64 myfunc(Float64 %x) {
    entry:
        %.1    = call_math(expm1, [%x]) -> Float64
        %.2    = ret(%.1) -> Void

    }


This is unfortunately a lot of code for a seemingly simple transformation!
In the future we hope to implement a proper rewrite engine.

Compiling to LLVM
=================

Below we show how to compile our example with LLVM. A more realistic example
arranges these passes in a pipeline and executes the entire pipeline, but
here we do it manually to show the result of each transformation.

.. code-block:: python

    >>> from pykit import environment
    >>> from pykit.codegen.llvm import llvm_codegen, llvm_postpasses
    >>> from pykit.codegen import llvm
    >>> import llvm.core as lc

    >>> # Allocate compilation environment, and prepare it for LLVM codegen
    >>> env = environment.fresh_env()
    >>> llvm.install(env)
    >>> llvm_func = llvm_codegen.initialize(func, env)

    >>> # Generate LLVM
    >>> lfunc = llvm_codegen.translate(func, env, llvm_func)
    >>> print(lfunc)
    define double @myfunc(double) {
    myfunc:
      %.1 = call double @"pykit.math.['Float64'].expm1"(double %0)
      ret double %.1
    }

    >>> # Resolve math functions
    >>> llvm_postpasses.run(lfunc, env)
    >>> print(lfunc)
    define double @myfunc(double) {
    myfunc:
      %.1 = call double @npy_expm1(double %0)
      ret double %.1
    }

    >>> # Verify and optimize the result
    >>> llvm.verify(lfunc, env)
    >>> llvm.optimize(lfunc, env)
    >>> print(lfunc)
    ; Function Attrs: nounwind
    define double @myfunc(double) #0 {
    myfunc:
      %1 = tail call double @expm1(double %0) #0
      ret double %1
    }

At the bottom we see how the LLVM optimizer inlined the implementation of
`npy_expm1`, exposed to LLVM through Clang-compiled bitcode.

Calling the Function!
=====================

In order to use the function, we need to get a pointer to it. We can then
wrap it in a ctypes function and use it from Python. We can use the
`get_ctypes` function which updates the environment with a ctypes function
according to the type of the function:

.. code-block:: python

    >>> from pykit import environment
    >>>
    >>> llvm.get_ctypes(lfunc, env)
    >>> cfunc = env["codegen.llvm.ctypes"]
    >>> cfunc(2.0)
    6.38905609893