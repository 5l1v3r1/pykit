# -*- coding: utf-8 -*-

"""
Convenience IR builder.
"""

from __future__ import print_function, division, absolute_import
from contextlib import contextmanager

from pykit import error
from pykit import types
from pykit.ir import Value, Const, Undef, ops, findop, FuncArg, blocks
from . import _generated

#===------------------------------------------------------------------===
# Helpers
#===------------------------------------------------------------------===

def unary(op):
    def unary(self, value0, **kwds):
        type = value0.type
        m = getattr(super(OpBuilder, self), op)
        return m(type, value0, **kwds)
    return unary

def binop(op, type=None):
    def binop(self, value0, value1, **kwds):
        assert value0.type == value1.type, (value0.type, value1.type)
        if type is None:
            ty = value0.type
        else:
            ty = type
        m = getattr(super(OpBuilder, self), op)
        return m(ty, value0, value1, **kwds)
    return binop

#===------------------------------------------------------------------===
# Builder
#===------------------------------------------------------------------===

class OpBuilder(_generated.GeneratedBuilder):
    """
    Build Operations, improving upon the generated methods.
    """

    def alloca(self, type,  **kwds):
        assert type is not None
        assert type.is_pointer
        return super(OpBuilder, self).alloca(type, **kwds)

    def load(self, value0, **kwds):
        type = value0.type
        assert type.is_pointer
        return super(OpBuilder, self).load(type.base, value0, **kwds)

    def store(self, val, var, **kwds):
        assert var.type.is_pointer
        assert val.type == var.type.base, (val.type, var.type)
        return super(OpBuilder, self).store(val, var, **kwds)

    def call(self, type, func, args, **kwds):
        return super(OpBuilder, self).call(type, func, args, **kwds)

    def ptradd(self, ptr, value, **kwds):
        type = ptr.type
        assert type.is_pointer
        return super(OpBuilder, self).ptradd(type, ptr, value, **kwds)

    def ptrload(self, ptr, **kwds):
        assert ptr.type.is_pointer
        return super(OpBuilder, self).ptrload(ptr.type.base, ptr, **kwds)

    def ptrstore(self, value, ptr, **kwds):
        assert ptr.type.is_pointer
        assert ptr.type.base == value.type
        return super(OpBuilder, self).ptrstore(value, ptr, **kwds)

    def ptr_isnull(self, ptr, **kwds):
        assert ptr.type.is_pointer
        return super(OpBuilder, self).ptr_isnull(types.Bool, ptr, **kwds)

    invert               = unary('invert')
    uadd                 = unary('uadd')
    not_                 = unary('not_')
    usub                 = unary('usub')
    add                  = binop('add')
    rshift               = binop('rshift')
    sub                  = binop('sub')
    lshift               = binop('lshift')
    mul                  = binop('mul')
    div                  = binop('div')
    bitor                = binop('bitor')
    bitxor               = binop('bitxor')
    bitand               = binop('bitand')
    mod                  = binop('mod')
    gt                   = binop('gt'      , type=types.Bool)
    is_                  = binop('is_'     , type=types.Bool)
    ge                   = binop('ge'      , type=types.Bool)
    ne                   = binop('ne'      , type=types.Bool)
    lt                   = binop('lt'      , type=types.Bool)
    le                   = binop('le'      , type=types.Bool)
    eq                   = binop('eq'      , type=types.Bool)


class Builder(OpBuilder):
    """
    I build Operations and emit them into the function.

    Also provides convenience operations, such as loops, guards, etc.
    """

    def __init__(self, func):
        self.func = func
        self.module = func.module
        self._curblock = None
        self._lastop = None

    def emit(self, op):
        """
        Emit an Operation at the current position.
        Sets result register if not set already.
        """
        assert self._curblock, "Builder is not positioned!"

        if op.result is None:
            op.result = self.func.temp()

        if self._lastop == 'head' and self._curblock.ops.head:
            op.insert_before(self._curblock.ops.head)
        elif self._lastop in ('head', 'tail'):
            self._curblock.append(op)
        else:
            op.insert_after(self._lastop)
        self._lastop = op

    def _insert_op(self, op):
        if self._curblock:
            self.emit(op)

    # __________________________________________________________________
    # Positioning

    @property
    def basic_block(self):
        return self._curblock

    def position_at_beginning(self, block):
        """Position the builder at the beginning of the given block."""
        self._curblock = block
        self._lastop = 'head'

    def position_at_end(self, block):
        """Position the builder at the end of the given block."""
        self._curblock = block
        self._lastop = block.tail or 'tail'

    def position_before(self, op):
        """Position the builder before the given op."""
        if isinstance(op, FuncArg):
            raise error.PositioningError(
                "Cannot place builder before function argument")
        self._curblock = op.block
        if op == op.block.head:
            self._lastop = 'head'
        else:
            self._lastop = op._prev

    def position_after(self, op):
        """Position the builder after the given op."""
        if isinstance(op, FuncArg):
            self.position_at_beginning(op.parent.startblock)
        else:
            self._curblock = op.block
            self._lastop = op

    @contextmanager
    def _position(self, block, position):
        curblock, lastop = self._curblock, self._lastop
        position(block)
        yield
        self._curblock, self._lastop = curblock, lastop

    at_front = lambda self, b: self._position(b, self.position_at_beginning)
    at_end   = lambda self, b: self._position(b, self.position_at_end)

    # __________________________________________________________________
    # Convenience

    def gen_call_external(self, fname, args, result=None):
        """Generate call to external function (which must be declared"""
        gv = self.module.get_global(fname)

        assert gv is not None, "Global %s not declared" % fname
        assert gv.type.is_function, gv
        assert gv.type.argtypes == [arg.type for arg in args]

        op = self.call(gv.type.res, [Const(fname), args])
        op.result = result or op.result
        return op

    def _find_handler(self, exc, exc_setup):
        """
        Given an exception and an exception setup clause, generate
        exc_matches() checks
        """
        catch_sites = [findop(block, 'exc_catch') for block in exc_setup.args]
        for exc_catch in catch_sites:
            for exc_type in exc_catch.args:
                with self.if_(self.exc_matches(types.Bool, [exc, exc_type])):
                    self.jump(exc_catch.block)
                    block = self._curblock
                self.position_at_end(block)

    def gen_error_propagation(self, exc=None):
        """
        Propagate an exception. If `exc` is not given it will be loaded
        to match in 'except' clauses.
        """
        assert self._curblock

        block = self._curblock
        exc_setup = findop(block.leaders, 'exc_setup')
        if exc_setup:
            exc = exc or self.load_tl_exc(types.Exception)
            self._find_handler(exc, exc_setup)
        else:
            self.gen_ret_undef()

    def gen_ret_undef(self):
        """Generate a return with undefined value"""
        type = self.func.type.restype
        if type.is_void:
            self.ret(None)
        else:
            self.ret(Undef(type))

    def splitblock(self, name=None, terminate=False, preserve_exc=True):
        """Split the current block, returning (old_block, new_block)"""
        oldblock = self._curblock
        op = self._lastop
        if op == 'head':
            trailing = list(self._curblock.ops)
        elif op != 'tail':
            trailing = list(op.block.ops.iter_from(op))[1:]
        else:
            trailing = []

        return blocks.splitblock(oldblock, trailing, name,
                                 terminate, preserve_exc)

    def _patch_phis(self, oldblock, newblock):
        """
        Patch phis when a predecessor block changes
        """
        for op in ops:
            for use in self.func.uses[op]:
                if use.opcode == 'phi':
                    # Update predecessor blocks
                    preds, vals = use.args
                    preds = [newblock if pred == oldblock else pred
                                 for pred in preds]
                    use.set_args([preds, vals])

    def if_(self, cond):
        """with b.if_(b.eq(a, b)): ..."""
        old, exit = self.splitblock()
        if_block = self.func.new_block("if_block", after=self._curblock)
        self.cbranch(cond, if_block, exit)
        return self.at_end(if_block)

    def ifelse(self, cond):
        old, exit = self.splitblock()
        if_block = self.func.new_block("if_block", after=self._curblock)
        el_block = self.func.new_block("else_block", after=if_block)
        self.cbranch(cond, if_block, el_block)
        return self.at_end(if_block), self.at_end(el_block), exit

    def gen_loop(self, start=None, stop=None, step=None):
        """
        Generate a loop given start, stop, step and the index variable type.
        The builder's position is set to the end of the body block.

        Returns (condition_block, body_block, exit_block).
        """
        assert isinstance(stop, Value), "Stop should be a Constant or Operation"

        ty = stop.type
        start = start or Const(0, ty)
        step  = step or Const(1, ty)
        assert start.type == ty == step.type

        with self.at_front(self.func.startblock):
            var = self.alloca(types.Pointer(ty))

        prev, exit = self.splitblock('loop.exit')
        cond = self.func.new_block('loop.cond', after=prev)
        body = self.func.new_block('loop.body', after=cond)

        with self.at_end(prev):
            self.store(start, var)
            self.jump(cond)

        # Condition
        with self.at_front(cond):
            index = self.load(var)
            self.store(self.add(index, step), var)
            self.cbranch(self.lt(index, stop), body, exit)

        with self.at_end(body):
            self.jump(cond)

        self.position_at_beginning(body)
        return cond, body, exit
