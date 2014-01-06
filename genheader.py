# -*- coding: utf-8 -*-

"""
    Generated builder methods.
"""

from __future__ import print_function, division, absolute_import

from pykit import types, config
from pykit.ir import Op, Value, Const, ops
from pykit.ir.verification import verify_op_syntax


class GeneratedBuilder(object):
    _const = lambda val: Const(val, types.Opaque)
    _insert_op = lambda self, op: None  # noop
