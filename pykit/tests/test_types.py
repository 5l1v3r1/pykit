# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit import types

def create():
    t = types.Struct([], [])
    t.names.extend(['spam', 'ham', 'eggs'])
    t.types.extend([types.Pointer(t), types.Int64, t])
    return t


class TestEquality(unittest.TestCase):

    def test_recursive_structs(self):
        t1 = create()
        t2 = create()
        self.assertEqual(t1, t2)

        t3 = create()
        t3.names.append('ham')
        t3.types.append(types.Int32)

        t4 = create()
        t4.names.append('ham')
        t4.types.append(types.Int64)

        self.assertNotEqual(t1, t3)
        self.assertNotEqual(t3, t4)

    def test_recursive_structs_format(self):
        self.assertEqual(str(create()), '{ spam:...*, ham:Int64, eggs:... }')

    def test_unit(self):
        self.assertEqual(types.Void, types.Void)
        self.assertEqual(types.Bool, types.Bool)
        self.assertEqual(types.Int32, types.Int32)
        self.assertEqual(types.Float32, types.Float32)
        self.assertEqual(types.Pointer(types.Int32),
                         types.Pointer(types.Int32))
        self.assertEqual(types.Vector(types.Int32, 4),
                         types.Vector(types.Int32, 4))


        self.assertNotEqual(types.Void, types.Bool)
        self.assertNotEqual(types.Pointer(types.Void),
                            types.Pointer(types.Bool))
        self.assertNotEqual(types.Vector(types.Int32, 4),
                            types.Vector(types.Int32, 5))
        self.assertNotEqual(types.Vector(types.Int32, 4),
                            types.Vector(types.Int64, 4))





if __name__ == '__main__':
    unittest.main()
