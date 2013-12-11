# -*- coding: utf-8 -*-

"""
Promote phi variables for stack variables.

We take the native approach by simply allocating a stack variable for each
phi variable, and generating store (copy) instructions in predecessor basic
blocks.

The main subtleties are:

    1) phis are executed in parallel (semantically)

        -> generate all loads before generating any copy instruction for
           phi operands. See the 'swap' problem outlined in Briggs et al.

    2) critical edges (edges from a predecessor with multiple successors, and
       a successor with multiple predecessors) are a problem, since we want to
       generate a copy for only one of the destinations in the predecessor

        -> split critical edges before generating copies


NOTE: This pass *does not work together with exceptions*! If this runs before
      expanding exceptional control flow without translation back into SSA,
      the results will be incorrect.


References:

[1]: Practical Improvements to the Construction and Destruction of Static Single
     Assignment Form, Briggs et al
[2]: Translating Out of Static Single Assignment Form, Sreedhar et al
[3]: Revisiting Out-of-SSA Translation for Correctness, Code Quality, and
     Eﬃciency, Boissinot et al
"""

from __future__ import print_function, division, absolute_import
import collections

from pykit import types
from pykit.ir import Builder, Op, ops
from pykit.analysis import cfa

#===------------------------------------------------------------------===
# Critical edges
#===------------------------------------------------------------------===

def split_critical_edges(func, cfg, phis):
    """
    Split critical edges to correctly handle cycles in phis. See 2) above.
    """
    b = Builder(func)
    for block in cfg.node:
        successors = cfg.neighbors(block)
        if len(successors) > 1:
            # More than one successor, we need to split
            # (Alternatively, we could move our copies into the successor block
            #  if we were the only predecessor, but this seems simpler)

            # Split successors with phis
            new_succs = {} # old_successor -> new_successor
            for succ in successors:
                if phis[succ]:
                    label = func.temp("split_critical")
                    new_succ = func.new_block(label, after=block)
                    new_succs[succ] = new_succ
                    b.position_at_end(new_succ)
                    b.jump(succ)

            # Patch our basic-block terminator to point to new blocks
            if new_succs:
                terminator = block.terminator
                assert terminator.opcode == 'cbranch', terminator
                test, truebb, falsebb = terminator.args
                terminator.set_args([test,
                                     new_succs.get(truebb, truebb),
                                     new_succs.get(falsebb, falsebb)])

#===------------------------------------------------------------------===
# SSA -> stack
#===------------------------------------------------------------------===

def generate_copies(func, phis):
    """
    Emit stores to stack variables in predecessor blocks.
    """
    builder = Builder(func)
    vars = {}
    loads = {}

    # Allocate a stack variable for each phi
    builder.position_at_beginning(func.startblock)
    for block in phis:
        for phi in phis[block]:
            vars[phi] = builder.alloca(types.Pointer(phi.type))

    # Generate loads in blocks containing the phis
    for block in phis:
        leaders = list(block.leaders)
        last_leader = leaders[-1] if leaders else block.head
        builder.position_after(last_leader)
        for phi in phis[block]:
            loads[phi] = builder.load(vars[phi])

    # Generate copies (store to stack variables)
    for block in phis:
        for phi in phis[block]:
            preds, args = phi.args
            var = vars[phi]
            phi_args = [loads.get(arg, arg) for arg in args]
            for pred, arg in zip(preds, phi_args):
                builder.position_before(pred.terminator)
                builder.store(arg, var)

    # Replace phis
    for block in phis:
        for phi in phis[block]:
            phi.replace_uses(loads[phi])
            phi.delete()

    return vars, loads

#===------------------------------------------------------------------===
# Driver
#===------------------------------------------------------------------===

def find_phis(func):
    """Map blocks to phis found in the block"""
    phis = {}
    for block in func.blocks:
        phis[block] = []
        for op in block.leaders:
            if op.opcode == 'phi':
                phis[block].append(op)

    return phis

def reg2mem(func, env=None):
    cfg = cfa.cfg(func, exceptions=False) # ignore exc_setup
    split_critical_edges(func, cfg, find_phis(func))
    vars, loads = generate_copies(func, find_phis(func))
    return vars, loads

def run(func, env):
    reg2mem(func, env)