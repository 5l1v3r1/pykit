from pykit.utils import hashable
from pykit.types import (Boolean, Integral, Float32, Float64, Array, Struct, Pointer,
                         Function, Vector, VoidT, resolve_typedef)
from llvm.core import Type, TYPE_FUNCTION

from llvmmath import llvm_support


def llvm_type(type, memo=None):
    if memo is None:
        memo = {}
    if hashable(type) and type in memo:
        return memo[type]

    ty = type.__class__
    if ty == Boolean:
        result = Type.int(1)
    elif ty == Integral:
        result = Type.int(type.bits)
    elif type == Float32:
        result = Type.float()
    elif type == Float64:
        result = Type.double()
    elif ty == Array:
        result = Type.array(llvm_type(type.base, memo), type.count)
    elif ty == Vector:
        result = Type.vector(llvm_type(type.base, memo), type.count)
    elif ty == Struct:
        result = handle_struct(type, memo)
    elif ty == Pointer:
        if type.base.is_void:
            return Type.pointer(Type.int(8))
        result = Type.pointer(llvm_type(type.base, memo))
    elif ty == Function:
        result = Type.function(
            llvm_type(type.restype, memo),
            [llvm_type(argtype, memo) for argtype in type.argtypes],
            var_arg=type.varargs)
    elif ty == VoidT:
        result = Type.void()
    else:
        raise TypeError("Cannot convert type %s" % (type,))

    memo[type] = result
    return result


opaque_memo = {}

def handle_struct(type, memo):
    # Check the cache with a hashable struct type
    key = type

    if key in memo:
        return memo[key]
    if key in opaque_memo:
        return opaque_memo[key]

    # Allocate and pre-order cache dummy struct
    struct_type = Type.opaque('dummy_struct_type')
    memo[key] = struct_type
    opaque_memo[key] = struct_type

    # Process fields and re-cache
    fields = [llvm_type(ftype, memo) for ftype in type.types]
    result = Type.struct(fields)
    struct_type.set_body([result])

    memo[key] = result
    opaque_memo[key] = result

    return result


def ctype(llvm_type):
    return llvm_support.map_llvm_to_ctypes(llvm_type)