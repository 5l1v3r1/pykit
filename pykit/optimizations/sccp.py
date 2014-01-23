# -*- coding: utf-8 -*-

"""
Sparse conditional constant propagation. LLVM already does a great job at
this, but we need this to be *extensible*, i.e. we may want to feed in
high-level information or aid type inference (exclude dead branches).

We assign each value a cell, which holds values from the lattice. We start
optimistically at the top (⊤), and take the meet of incoming values at
joins, which means we can only move down the lattice. The bottom (⊥)
indicates a runtime value.

                                    ⊤
                                  / | \
                                c1 c2  c3
                                  \ | /
                                    ⊥

If we instead were to start at the bottom by assuming everything were a
runtime value unless proven otherwise, we would not be able to resolve
cycles of φ nodes, which wouldn't handle loops. The simplest example would be

                              φ0 = φ(5, φ0)

which is a self-dependence -- since φ0 is determined ⊥, the meet must also be ⊥.

See also 'Constant Propagation with Conditional Branches' by
M. N. Wegman and F. K. Zadeck.
"""

from functools import partial
from collections import defaultdict, deque

from pykit import types
from pykit.analysis import cfa
from pykit.ir import Op, Const, vmap

#===------------------------------------------------------------------===
# SCCP
#===------------------------------------------------------------------===

class LatticeValue(object):
    def __init__(self, value):
        self.value = value

    def __unicode__(self):
        return unicode(self.value)

    def __repr__(self):
        return unicode(self).encode('UTF-8')

top = LatticeValue(u'⊤')
bottom = LatticeValue(u'⊥')
cell = lambda: top
isconst = lambda x: x not in (top, bottom)
unwrap = lambda x: x.const if isinstance(x, Const) else x

def sccp(func, constantfolder=None):
    """
    Perform Sparse conditional constant propagation. The idea is to have two
    queues, one for blocks and one for SSA variables (Ops).
    Blocks must be processed whole, which is a dense operation. Subsequent
    changes to live code are then sparse operations using the SSA info.

    When reaching the end of a block started by a CFG edge,
    we add new edges iff we have an unconditional branch. After all, we are
    executing optimistically, which means we cannot tell whether the
    destination blocks are live.

    Note that we can perform no modifications until after the algorithm
    terminates, since the cells are only correct after termination.

    Returns
    =======
    constmap: A dict mapping Ops to Consts
    deadblock: A set of dead basic blocks
    """
    # Object that folds operations with constant inputs
    constantfolder = constantfolder or ConstantFolder()

    # Mapping of CFG edges (block1, block2) to indicate whether there exists
    # some runtime path from block1 to block2. Blocks without any incoming
    # runtime path are not explored.
    executable = defaultdict(bool)

    # Control flow graph (networkx.DiGraph)
    cfg = cfa.cfg(func)

    cfedges = deque([(None, func.startblock)]) # remaining cfg edges
    ssavars = deque()           # SSA edges: (Op, Op)
    cells   = defaultdict(cell) # Cells holding lattice values
    processed = set()           # Set of processed blocks

    # Initialize all constants in cells
    vmap(partial(initialize, cells), func)

    while cfedges or ssavars:
        if cfedges:
            src, dst = cfedges.popleft()
            if not executable[src, dst]:
                # Process each block only once for each predecessor
                executable[src, dst] = True
                # process_phis(dst, constantfolder, cells, ssavars)
                if dst not in processed:
                    # This is the first time we visit this block, process body
                    processed.add(dst)
                    process_body(constantfolder, dst, cfg, cells, ssavars, cfedges)

        else:
            defop, op = ssavars.popleft()
            if executable[defop.block, op.block]:
                # Only handle live code !
                process_expr(constantfolder, op, cells, ssavars)

    deadblocks = set(func.blocks) - processed
    return deadblocks, cells, cfg


def initialize(cells, value):
    """Initialize lattice cells with constants"""
    if isinstance(value, Const):
        cells[value] = value


def meet(x, y):
    """Meet operation on our lattice"""
    if x == top:
        return y
    elif y == top:
        return x
    elif x == bottom or y == bottom:
        return bottom
    elif x != y:
        return bottom
    else:
        return x # x == y


def process_body(folder, block, cfg, cells, ssavars, cfedges):
    """Process a new executable basic block"""
    for op in block:
        process_expr(folder, op, cells, ssavars)

    op = block.terminator
    successors = cfg.neighbors(block)

    if op.opcode == 'cbranch':
        # -------------------------------------------------
        # Add successors of conditional branch

        test, trueblock, falseblock = op.args
        value = cells[test]
        # Depending on the value (constant or bottom) add only one, or add
        # all branches
        if isconst(value):
            assert value.type == types.Bool, value.type
            dst = [falseblock, trueblock][value.const]
            cfedges.append((op.block, dst))
            return

    elif op.opcode == 'exc_throw':
        # TODO: based on a static type, add only that successor
        #       Alternatively, rewrite local use of exc_throw to jumps first
        pass

    # -------------------------------------------------
    # Add successors for cbranch(⊥, ...), ret, jump, exc_throw

    cfedges.extend((block, succ) for succ in successors)

def process_phis(block, folder, cells, ssavars):
    for op in block.leaders:
        if op.opcode == 'phi':
            process_expr(folder, op, cells, ssavars)

def process_expr(folder, op, cells, ssavars):
    curval = cells[op]
    newval = folder.fold(op, cells)
    if curval != newval:
        ssavars.extend((op, use) for use in op.uses)

#===------------------------------------------------------------------===
# Constant Folding
#===------------------------------------------------------------------===

class ConstantFolder(object):
    """Fold constants!"""

    def fold(self, op, cells):
        m = getattr(self, 'op_' + op.opcode, None)
        result = None
        if m is not None:
            result = m(op, cells)
            if (result is not None and isconst(result) and not
                    isinstance(result, Const)):
                result = Const(result, op.type)
                cells[result] = result

        if result is None:
            result = bottom # Undetermined value

        cells[op] = result
        return result

    def op_phi(self, op, cells):
        blocks, args = op.args
        return reduce(meet, [unwrap(cells[arg]) for arg in args])

    def op_add(self, op, cells):
        left, right = op.args
        if isconst(cells[left]) and isconst(cells[right]):
            return cells[left].const + cells[right].const

    def op_lt(self, op, cells):
        left, right = op.args
        if isconst(cells[left]) and isconst(cells[right]):
            return cells[left].const < cells[right].const

    def op_convert(self, op, cells):
        return cells[op.args[0]]

#===------------------------------------------------------------------===
# Apply Result of SCCP
#===------------------------------------------------------------------===

def apply_result(func, cfg, deadblocks, cells):
    """
    Apply the result of the SCCP analysis:

        - replace ops with constants
        - remove unreachable code blocks
    """
    for op in func.ops:
        if isconst(cells[op]):
            op.replace_uses(cells[op])
            op.delete()
        if op.opcode == 'cbranch' and isconst(cells[op.args[0]]):
            test = cells[op.args[0]].const
            blocks = {True: op.args[1], False: op.args[2] }
            target = blocks[test]
            other  = blocks[not test]
            cfg.remove_edge(op.block, other)
            op.replace(Op("jump", types.Void, [target], op.result))

    cfa.delete_blocks(func, cfg, deadblocks)

#===------------------------------------------------------------------===
# run
#===------------------------------------------------------------------===

def run(func, env=None, constantfolder=None):
    deadblocks, cells, cfg = sccp(func, constantfolder)
    apply_result(func, cfg, deadblocks, cells)