# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit import types

def create():
    t = types.Struct([], [])
    t.names.extend(['spam', 'ham', 'eggs'])
    t.types.extend([types.Pointer(t), types.Int64, t])
    return t


class TestStructs(unittest.TestCase):

    def test_recursive_structs(self):
        self.assertEqual(create(), create())

    def test_recursive_structs_format(self):
        self.assertEqual(str(create()), '{ spam:...*, ham:Int64, eggs:... }')


if __name__ == '__main__':
    unittest.main()