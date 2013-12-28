cimport cython
from pykit.adt.linkedlist cimport LinkedList

cdef class Value(object):
    pass

cdef class Module(Value):
    pass

cdef class Function(Value):
    cdef public Module module
    cdef public str name
    cdef public LinkedList blocks
    cdef public list argnames
    cdef public dict blockmap, argdict, uses
    cdef public object temp

cdef class Block(Value):
    cdef public str name
    cdef public Module parent
    cdef public LinkedList ops

cdef class Local(Value):
    cdef public str opcode
    cdef public object type

cdef class FuncArg(Local):
    cdef public Function parent
    cdef public str result

cdef class Operation(Value):
    cdef public Function parent
    cdef public str result

    cdef object _args, _prev, _next, _metadata

cdef class Constant(Value):
    cdef public str opcode
    cdef public type, args, result

cdef class Pointer(Value):
    cdef public addr, type

cdef class Struct(Value):
    cdef public names, values, type

cdef class Undef(Value):
    cdef public type