# -*- coding: utf-8 -*-

"""
Pretty print pykit IR.
"""

from __future__ import print_function, division, absolute_import
from pykit.utils import hashable

prefix = lambda s: '%' + s
indent = lambda s: '\n'.join('    ' + s for s in s.splitlines())
ejoin  = "".join
sjoin  = " ".join
ajoin  = ", ".join
njoin  = "\n".join
parens = lambda s: '(' + s + ')'

compose = lambda f, g: lambda x: f(g(x))

def pretty(value):
    formatter = formatters[type(value).__name__]
    return formatter(value)

def fmod(mod):
    gs, fs = mod.globals.values(), mod.functions.values()
    return njoin([njoin(map(pretty, gs)), "", njoin(map(pretty, fs))])

def ffunc(f):
    restype = ftype(f.type.restype)
    types, names = map(ftype, f.type.argtypes), map(prefix, f.argnames)
    args = ajoin(map(sjoin, zip(types, names)))
    header = sjoin(["function", restype, f.name + parens(args)])
    return njoin([header + " {", njoin(map(fblock, f.blocks)), "}"])

def farg(func_arg):
    return "%" + func_arg.result

def fblock(block):
    body = njoin(map(compose(indent, fop), block))
    return njoin([block.name + ':', body, ''])

def _farg(oparg):
    from pykit import ir

    if isinstance(oparg, (ir.Function, ir.Block)):
        return prefix(oparg.name)
    elif isinstance(oparg, list):
        return "[%s]" % ", ".join(_farg(arg) for arg in oparg)
    elif isinstance(oparg, ir.Op):
        return prefix(str(oparg.result))
    else:
        return str(oparg)

def fop(op):
    body = "%s(%s)" % (op.opcode, ajoin(map(_farg, op.args)))
    return '%%%-5s = %s -> %s' % (op.result, body, ftype(op.type))

def fconst(c):
    return 'const(%s, %s)' % (c.const, ftype(c.type))

def fglobal(val):
    return "global %{0} = {1}".format(val.name, ftype(val.type))

def fundef(val):
    return '((%s) Undef)' % (val.type,)

def ftype(val, seen=None):
    from pykit import types

    if not isinstance(val, types.Type):
        return str(val)

    if seen is None:
        seen = set()
    if id(val) in seen:
        return '...'

    seen.add(id(val))

    if hashable(val) and val in types.type2name:
        result = types.type2name[val]
    elif val.is_struct:
        args = ", ".join('%s:%s' % (name, ftype(ty, seen))
                         for name, ty in zip(val.names, val.types))
        result = '{ %s }' % args
    elif val.is_pointer:
        result ="%s*" % (ftype(val.base, seen),)
    else:
        result = repr(val)

    seen.remove(id(val))
    return result

def fptr(val):
    return repr(val)

def fstruct(val):
    return repr(val)


formatters = {
    'Module':      fmod,
    'GlobalValue': fglobal,
    'Function':    ffunc,
    'FuncArg':     farg,
    'Block':       fblock,
    'Operation':   fop,
    'Constant':    fconst,
    'Undef':       fundef,
    'Pointer':     fptr,
    'Struct':      fstruct,
}