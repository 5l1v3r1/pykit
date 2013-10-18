# -*- coding: utf-8 -*-

"""
Support for ctypes.
"""

from __future__ import print_function, division, absolute_import

import ctypes.util

from pykit import types
from pykit.ir import Const, Struct, Pointer
from pykit.utils import hashable

#===------------------------------------------------------------------===
# CTypes Types for Type Checking
#===------------------------------------------------------------------===

_ctypes_scalar_type = type(ctypes.c_int)
_ctypes_func_type = type(ctypes.CFUNCTYPE(ctypes.c_int))
_ctypes_pointer_type = type(ctypes.POINTER(ctypes.c_int))
_ctypes_array_type = type(ctypes.c_int * 2)

CData = type(ctypes.c_int(10)).__mro__[-2]

#===------------------------------------------------------------------===
# Check Whether values are ctypes values
#===------------------------------------------------------------------===

def is_ctypes_function(value):
    return isinstance(type(value), _ctypes_func_type)

def is_ctypes_value(ctypes_value):
    return isinstance(ctypes_value, CData)

def is_ctypes_struct_type(ctypes_type):
    return (isinstance(ctypes_type, type) and
            issubclass(ctypes_type, ctypes.Structure))

def is_ctypes_pointer_type(ctypes_type):
    return isinstance(ctypes_type, _ctypes_pointer_type)

def is_ctypes_type(ctypes_type):
    return (
       (isinstance(ctypes_type, _ctypes_scalar_type)) or
       is_ctypes_struct_type(ctypes_type)
    )

def is_ctypes(value):
    "Check whether the given value is a ctypes value"
    return is_ctypes_value(value) or is_ctypes_type(value)

#===------------------------------------------------------------------===
# Type mapping (ctypes -> numba)
#===------------------------------------------------------------------===

ctypes_map = {
    ctypes.c_bool :  types.Bool,
    ctypes.c_int8 :  types.Int8,
    ctypes.c_int16:  types.Int16,
    ctypes.c_int32:  types.Int32,
    ctypes.c_int64:  types.Int64,
    ctypes.c_uint8 : types.UInt8,
    ctypes.c_uint16: types.UInt16,
    ctypes.c_uint32: types.UInt32,
    ctypes.c_uint64: types.UInt64,
    ctypes.c_float:  types.Float32,
    ctypes.c_double: types.Float64,
    None:            types.Void,
}

def from_ctypes_type(ctypes_type):
    """
    Convert a ctypes type to a pykit type.

    Supported are structs, unit types (int/float)
    """
    if hashable(ctypes_type) and ctypes_type in ctypes_map:
        return ctypes_map[ctypes_type]
    elif ctypes_type is ctypes.c_void_p:
        return types.Pointer(types.Void)
    elif is_ctypes_pointer_type(ctypes_type):
        return types.Pointer(from_ctypes_type(ctypes_type._type_))
    elif is_ctypes_struct_type(ctypes_type):
        fields = [(name, from_ctypes_type(field_type))
                      for name, field_type in ctypes_type._fields_]
        fieldnames, fieldtypes = zip(*fields) or (('dummy',), (types.Int8,))
        return types.Struct(fieldnames, fieldtypes)
    else:
        raise NotImplementedError(ctypes_type)

def from_ctypes_value(ctypes_value):
    """
    Convert a ctypes value to a pykit constant
    """
    if not is_ctypes_value(ctypes_value):
        assert isinstance(ctypes_value, (int, long, float))
        return Const(ctypes_value)

    ctype = type(ctypes_value)

    if hashable(ctype) and ctype in ctypes_map:
        return Const(ctypes_value.value, from_ctypes_type(ctype))
    elif is_ctypes_struct_type(ctype):
        names = [name for name, _ in ctype._fields_]
        values = [from_ctypes_value(getattr(ctypes_value, name)) for n in names]
        if not names:
            names, values = ('dummy',), (Const(0, types.Int8))
        return Struct(name, values)
    else:
        assert is_ctypes_pointer_type(ctype)
        return Pointer(ctypes.cast(ctypes_value, ctypes.c_void_p).value,
                       from_ctypes_type(ctype))