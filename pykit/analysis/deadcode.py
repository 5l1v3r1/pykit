# -*- coding: utf-8 -*-

"""
Identify dead code for elimination.
"""

effect_free = set([
    'alloca', 'load', 'new_exc', 'phi',
    'ptrload', 'ptrcast', 'ptr_isnull', 'getfield', 'getindex',
    'add', 'sub', 'mul', 'div', 'mod', 'lshift', 'rshift', 'bitand', 'bitor',
    'bitxor', 'invert', 'not_', 'uadd', 'usub', 'eq', 'ne', 'lt', 'le',
    'gt', 'ge', 'addressof',
])

def identify_dead_ops(func):
    """
    Identify dead code.
    """
    dead = set()
    for op in func.ops:
        if op.opcode in effect_free and len(func.uses[op]) == 0:
            dead.add(op)
    return dead
