# -*- coding: utf-8 -*-

"""
C code generation.
"""

from __future__ import print_function, division, absolute_import

import sys
from functools import partial

from pykit import error, types
from pykit import ir
from pykit.ir import vvisit, ArgLoader, verify_lowlevel
from pykit.ir import defs, opgrouper
from pykit.types import Boolean, Integral, Real, Pointer, Function, Int64, Struct
from pykit.codegen.c.c_types import c_type
from pykit.utils import make_temper

#===------------------------------------------------------------------===
# Translator
#===------------------------------------------------------------------===

class Translator(object):
    """
    Translate a function in low-level form.
    This means it can only use values of type Bool, Int, Float, Struct or
    Pointer. Values of type Function may be called.
    """

    def __init__(self, func, env, emit):
        self.func = func
        self.env = env
        self.emit = emit

    def emit_expr(self, op, fmt, *args):
        lhs = op.result
        rhs = format(fmt, *args)
        self.assign(lhs, rhs)
        return lhs

    def assign(self, lhs, rhs):
        self.emit(format("{0} = {1};", lhs, rhs))

    # __________________________________________________________________

    def op_arg(self, arg):
        return arg.result

    # __________________________________________________________________

    def op_unary(self, op, arg):
        unop = defs.unary_opcodes[op.opcode]
        return self.emit_expr(op, "{0} {1}", unop, arg)

    def op_binary(self, op, left, right):
        binop = defs.binary_opcodes[op.opcode]
        return self.emit_expr(op, "{0} {1} {2}", left, binop, right)

    def op_compare(self, op, left, right):
        cmpop = defs.compare_opcodes[op.opcode]
        return self.emit_expr(op, "{0} {1} {2}", left, cmpop, right)

    # __________________________________________________________________

    def op_convert(self, op, arg):
        if op.args[0].type == op.type:
            return arg
        return self.emit_expr(op, "{0} {1}", c_type(op.type), arg)

    # __________________________________________________________________

    def op_call(self, op, function, args):
        return self.emit_expr(op, "{0}({1})", function, ", ".join(args))

    def op_call_math(self, op, name, args):
        # Math is resolved by an LLVM postpass
        return self.op_call(op, name.lower(), args)

    # __________________________________________________________________

    def op_getfield(self, op, p, attr):
        return self.emit_expr(op, "(*{0}).{1}", p, attr)

    def op_setfield(self, op, p, attr, value):
        return self.emit("(*{0}).{1} = value;", p, attr, value)

    # __________________________________________________________________

    def op_extractfield(self, op, struct, attr):
        return self.emit_expr(op, "{0}.{1}", struct, attr)

    def op_insertfield(self, op, struct, attr, value):
        self.assign(op, struct)
        self.emit("{0}.{1} = {2};", struct, attr, value)

    # __________________________________________________________________

    def op_getindex(self, op, array, indices):
        return self.emit_expr(op, "{0}[{1}]", array, ", ".join(indices))

    def op_setindex(self, op, array, indices, value):
        self.emit("{0}[{1}] = {2};", array, ", ".join(indices), value)

    # __________________________________________________________________

    def op_alloca(self, op):
        self.emit("{0} {1};", c_type(op.type), op.result)
        return format("(&{0})", op.result)

    def op_load(self, op, stackvar):
        return self.emit_expr(op, "(*{0})", stackvar)

    def op_store(self, op, value, stackvar):
        self.emit("(*{0}) = {1};", stackvar, value)

    # __________________________________________________________________

    def op_jump(self, op, block):
        self.emit("goto {0};", block.name)

    def op_cbranch(self, op, test, true_block, false_block):
        self.emit("if ({0}) goto {1};", test, true_block.name)
        self.emit("else goto {2};", false_block.name)

    def op_phi(self, op):
        raise NotImplementedError

    def op_ret(self, op, value):
        return self.emit("return {0};", value)

    # __________________________________________________________________

    def op_sizeof(self, op, expr):
        raise NotImplementedError

    def op_addressof(self, op, func):
        raise NotImplementedError

    # __________________________________________________________________

    def op_ptradd(self, op, ptr, val):
        return self.emit_expr(op, "{0} + {1}", ptr, val)

    def op_ptrload(self, op, ptr):
        return self.emit_expr(op, "*{0}", ptr)

    def op_ptrstore(self, op, val, ptr):
        self.emit("*{0} = {1};", ptr, val)

    def op_ptrcast(self, op, val):
        type = c_type(op.type)
        return self.emit_expr(op, "({0}) {1}", type, val)

    def op_ptr_isnull(self, op, val):
        return self.emit_expr(op, "{0} == NULL", val)

    # __________________________________________________________________

    def op_exc_setup(self, op, *args):
        raise error.CompileError("exc_setup should have been replaced")

    def op_exc_throw(self, op, *args):
        raise error.CompileError("exc_throw should have been replaced")

    def op_exc_catch(self, op, *args):
        raise error.CompileError("exc_catch should have been replaced")


#===------------------------------------------------------------------===
# Argument loading
#===------------------------------------------------------------------===

class CArgLoader(ArgLoader):
    """
    Load Operation arguments as LLVM values passed and extra *args to the
    Translator.
    """

    def load_GlobalValue(self, arg):
        if arg.external:
            pass
        else:
            assert arg.value
            value = arg.value.const

        return value

    def load_Block(self, arg):
        return arg.name

    def load_Constant(self, arg):
        return make_constant(arg.const, arg.type)

    def load_Pointer(self, arg):
        raise NotImplementedError

    def load_Struct(self, arg):
        return make_constant(arg, arg.type)

    def load_Undef(self, arg):
        if arg.type.is_struct:
            return "{}"
        elif arg.type.is_int or arg.type.is_float:
            return "0"
        else:
            raise NotImplementedError("Undef for type %s" % (arg.type,))


def unwrap(c):
    if isinstance(c, ir.Const):
        return c.const
    return c

def make_constant(value, ty):
    cty = c_type(ty)
    if type(ty) == Pointer:
        value = value.addr
        if value == 0:
            return "NULL"
        elif isinstance(value, (int, long)):
            return format("({0} {1})", cty, value)
        else:
            raise ValueError(
                "Cannot create constant pointer to value '%s'" % (value,))
    elif type(ty) == Integral:
        return str(value)
    elif type(ty) == Real:
        return str(value)
    elif type(ty) == Boolean:
        return str(int(value))
    elif type(ty) == Struct:
        raise NotImplementedError
    else:
        raise NotImplementedError("Constants for", type(ty))

#===------------------------------------------------------------------===
# Entry points
#===------------------------------------------------------------------===

mangle = make_temper()

def initialize(func, env):
    return func

def translate(func, env, _):
    emit = lambda s, *args: sys.stdout.write(format(s, *args) + "\n")

    # -- Create visitor -- #
    translator = Translator(func, env, emit)
    visitor = opgrouper(translator)

    # -- Codegen -- #
    argloader = CArgLoader()
    valuemap = vvisit(visitor, func, argloader)