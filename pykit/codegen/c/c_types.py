# -*- coding: utf-8 -*-

"""
Translate pykit types to C types.
"""

from __future__ import print_function, division, absolute_import

from pykit.types import (Boolean, Integral, Float32, Float64, Struct, Pointer,
                         Function, VoidT, resolve_typedef)

def c_type(type):
    ty = type.__class__
    if ty == Boolean:
        return "int8"
    elif ty == Integral:
        if ty.unsigned:
            prefix = "u"
        else:
            prefix = ""
        return "%sint%d_t" % (prefix, type.bits)
    elif type == Float32:
        return "float"
    elif type == Float64:
        return "double"
    elif ty == Struct:
        fields = [c_type(ftype) for ftype in type.types]
        raise NotImplementedError
    elif ty == Pointer:
        return c_type(type.base)
    elif ty == Function:
        resty  = c_type(type.restype)
        params = [c_type(argtype) for argtype in type.argtypes]
        raise NotImplementedError
    elif ty == VoidT:
        return "void"
    else:
        raise TypeError("Cannot convert type %s" % (type,))
