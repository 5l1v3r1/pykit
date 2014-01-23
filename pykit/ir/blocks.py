# -*- coding: utf-8 -*-

"""
Utilities to work with basic blocks.
"""

from __future__ import print_function, division, absolute_import

#===------------------------------------------------------------------===
# Helpers
#===------------------------------------------------------------------===

def splitblock(block, trailing, name=None, terminate=False, preserve_exc=True):
    """Split the current block, returning (old_block, new_block)"""
    from pykit.analysis import cfa
    from pykit.ir import Builder

    func = block.parent

    if block.is_terminated():
        successors = cfa.deduce_successors(block)
    else:
        successors = []

    # -------------------------------------------------
    # Sanity check

    # Allow splitting only after leaders and before terminator
    # TODO: error check

    # -------------------------------------------------
    # Split

    blockname = name or func.temp('Block')
    newblock = func.new_block(blockname, after=block)

    # -------------------------------------------------
    # Move ops after the split to new block

    for op in trailing:
        op.unlink()
    newblock.extend(trailing)

    if terminate and not block.is_terminated():
        # Terminate
        b = Builder(func)
        b.position_at_end(block)
        b.jump(newblock)

    # Update phis and preserve exception blocks
    patch_phis(block, newblock, successors)
    if preserve_exc:
        preserve_exceptions(block, newblock)

    return block, newblock


def preserve_exceptions(oldblock, newblock):
    """
    Preserve exc_setup instructions for block splits.
    """
    from pykit.ir import Builder

    func = oldblock.parent
    b = Builder(func)
    b.position_at_beginning(newblock)

    for op in oldblock.leaders:
        if op.opcode == 'exc_setup':
            b.exc_setup(op.args[0], **op.metadata)


def patch_phis(oldblock, newblock, successors):
    """
    Patch phis when a predecessor block changes
    """
    for succ in successors:
        for op in succ.leaders:
            if op.opcode == 'phi':
                # Update predecessor blocks
                preds, vals = op.args
                preds = [newblock if pred == oldblock else pred
                             for pred in preds]
                op.set_args([preds, vals])