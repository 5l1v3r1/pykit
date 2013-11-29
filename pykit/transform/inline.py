# -*- coding: utf-8 -*-

"""
Function inlining.
"""

from __future__ import print_function, division, absolute_import

from pykit.error import CompileError
from pykit.analysis import loop_detection
from pykit.ir import Function, Builder, findallops, copy_function, verify
from pykit.transform import ret as ret_normalization

def rewrite_return(func):
    """Rewrite ret ops to assign to a variable instead, which is returned"""
    ret_normalization.run(func)
    [ret] = findallops(func, 'ret')
    [value] = ret.args
    ret.delete()
    return value

def inline(func, call):
    """
    Inline the call instruction into func.

    :return: { old_op : new_op }
    """
    callee = call.args[0]
    callblock = call.block
    # assert_inlinable(func, call, callee, uses)

    builder = Builder(func)
    builder.position_before(call)
    inline_header, inline_exit = builder.splitblock()
    new_callee, valuemap = copy_function(callee, temper=func.temp)
    result = rewrite_return(new_callee)

    # Fix up arguments
    for funcarg, arg in zip(new_callee.args, call.args[1]):
        funcarg.replace_uses(arg)

    # Copy blocks
    new_blocks = list(new_callee.blocks)
    after = inline_header
    for block in new_blocks:
        block.parent = None
        func.add_block(block, after=after)
        after = block

    # Fix up wiring
    builder.jump(new_callee.startblock)
    with builder.at_end(new_callee.exitblock):
        builder.jump(inline_exit)

    stretch_exception_block(builder, callblock, new_blocks)

    # Fix up final result of call
    if result is not None:
        # non-void return
        result.unlink()
        result.result = call.result
        call.replace(result)
    else:
        call.delete()

    func.reset_uses()
    verify(func)

    return valuemap


def stretch_exception_block(builder, originating_block, new_blocks):
    """
    Replicate exc_setup across `new_blocks` that were introduced from
    `originating_block` by inlining.
    """
    # Replicate exc_setup
    setups = [op for op in originating_block.leaders if op.opcode == 'exc_setup']
    for block in new_blocks:
        builder.position_at_beginning(block)
        for setup in setups:
            builder.exc_setup(setup.args[0])

    for setup in setups:
        [successors] = setup.args # exception handling blocks

        # Patch phis in exception handling blocks for new predecessors
        for successor in successors:
            for op in successor.leaders:
                if op.opcode == 'phi':
                    blocks, values = map(list, op.args)

                    # Find value for original predecessor
                    idx = blocks.index(originating_block)
                    value = values[idx]

                    # Patch value for new predecessors
                    for block in new_blocks:
                        if block not in blocks:
                            # We found a new predecessor!
                            blocks.append(block)
                            values.append(value)

                    op.set_args([blocks, values])


def assert_inlinable(func, call, callee, uses):
    """
    Verify that a function call can be inlined.

    We can inline generators if they are consumed in a single loop:

        - iter(g) must be in a loop header
        - next(g) must be in the loop body

    :return: None if inlineable, or an exception with a message
    """
    if not isinstance(callee, Function):
        return CompileError("Cannot inline external function: %s" % (callee,))

    yields = findallops(callee, 'yield')
    if yields:
        for use in uses[call]:
            if use.opcode not in ('iter', 'next'):
                return CompileError(
                    "Cannot inline generator with use %s" % (use,))

        if len(uses[call]) != 2:
            return CompileError("Can only")
        loops = loop_detection.find_natural_loops(func)
