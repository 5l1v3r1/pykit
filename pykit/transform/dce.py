# -*- coding: utf-8 -*-

"""
Dead code elimination.
"""

effect_free = set([
    'alloca', 'load', 'new_exc', 'phi',
    'ptrload', 'ptrcast', 'ptr_isnull', 'getfield', 'getindex',
    'add', 'sub', 'mul', 'div', 'mod', 'lshift', 'rshift', 'bitand', 'bitor',
    'bitxor', 'invert', 'not_', 'uadd', 'usub', 'eq', 'ne', 'lt', 'le',
    'gt', 'ge', 'addressof',
])

def dce(func, env=None):
    """
    Eliminate dead code.

    TODO: Prune branches, dead loops
    """
    for op in func.ops:
        if op.opcode in effect_free and len(func.uses[op]) == 0:
            op.delete()

run = dce