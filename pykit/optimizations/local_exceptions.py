# -*- coding: utf-8 -*-

"""
Rewrite exceptions that are thrown and caught locally to jumps.
"""

from pykit.ir import interp, Const, OpBuilder, findallops

def find_handler(setup_handlers, exc_model, exc):
    for exc_setup in setup_handlers:
        [handler_blocks] = exc_setup.args
        for block in handler_blocks:
            for op in findallops(block.leaders, 'exc_catch'):
                [exc_types] = op.args
                if any(exc_model.exc_op_match(exc_type, exc)
                           for exc_type in exc_types):
                    return op.block


def rewrite_exceptions(func, env, exc_model=interp.ExceptionModel()):
    """
    Rewrite exc_throw(exc) -> jump(handler_block) for statically determined
    exceptions.

    TODO: Can this be optimized instead after lowering to a zero-cost or
          costful model?
    """
    b = OpBuilder()
    for op in func.ops:
        if op.opcode != 'exc_throw':
            continue
        [exc] = op.args
        setup_handlers = findallops(op.block.leaders, 'exc_setup')
        handler = find_handler(setup_handlers, exc_model, exc)
        if handler:
            op.replace(b.jump(handler, result=op.result))


run = rewrite_exceptions