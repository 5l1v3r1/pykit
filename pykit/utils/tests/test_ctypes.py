# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import ctypes
import unittest

from pykit import types
from pykit import ir
from pykit.utils.ctypes import from_ctypes_type, from_ctypes_value

class MyStruct(ctypes.Structure):
    _fields_ = [('x', ctypes.c_float), ('y', ctypes.c_int64)]

class TestCTypes(unittest.TestCase):

    def test_type(self):
        self.assertEqual(from_ctypes_type(ctypes.c_int32), types.Int32)
        self.assertEqual(from_ctypes_type(ctypes.POINTER(ctypes.c_int32)),
                         types.Pointer(types.Int32))
        self.assertEqual(from_ctypes_type(MyStruct),
                         types.Struct(('x', 'y'), (types.Float32, types.Int64)))

    def test_value(self):
        self.assertEqual(from_ctypes_value(ctypes.c_int32(10)),
                         ir.Const(10, types.Int32))

        i = ctypes.c_int32(10)
        p = ctypes.pointer(i)
        addr = ctypes.cast(p, ctypes.c_void_p).value
        self.assertEqual(from_ctypes_value(p), ir.Pointer(addr))
        #self.assertEqual(from_ctypes_type(MyStruct),
        #                 types.Struct(('x', 'y'), (types.Float32, types.Int64)))


if __name__ == '__main__':
    unittest.main()