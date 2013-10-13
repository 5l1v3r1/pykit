# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit.parsing import cirparser
from pykit.ir import verify, interp

source = """
#include <pykit_ir.h>

Int32 myglobal = 10;

Int32 myfunc(float x) {
    Int32 y;
    Int32 i = 10;

    y = 4;
    while (y < i) {
        y = (Int32) y + 1;
        (void) print(myglobal);
    }

    return y + 2;
}
"""

class TestParser(unittest.TestCase):
    def test_parse(self):
        mod = cirparser.from_c(source)
        verify(mod)
        func = mod.get_function('myfunc')
        result = interp.run(func, args=[10.0])
        self.assertEqual(result, 12)


if __name__ == '__main__':
    unittest.main()