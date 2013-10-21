# -*- coding: utf-8 -*-

"""
Dead code elimination.
"""

from pykit.analysis import deadcode

def dce(func, env=None):
    """
    Eliminate dead code.
    """
    for op in deadcode.identify_dead_ops(func):
        op.delete()

run = dce