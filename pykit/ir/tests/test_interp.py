# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from pykit.parsing import cirparser
from pykit.ir import verify, interp

source = """
#include <pykit_ir.h>

Int32 myglobal = 10;

float simple(float x) {
    return x * x;
}

Int32 loop() {
    Int32 i, sum = 0;
    for (i = 0; i < 10; i = i + 1) {
        sum = sum + i;
    }
    return sum;
}

Int32 raise() {
    Exception exc = new_exc("TypeError", "");
    exc_throw(exc);
    return 0;
}
"""

mod = cirparser.from_c(source)
verify(mod)

class TestInterp(unittest.TestCase):

    def test_simple(self):
        f = mod.get_function('simple')
        result = interp.run(f, args=[10.0])
        assert result == 100.0, result

    def test_loop(self):
        loop = mod.get_function('loop')
        result = interp.run(loop)
        assert result == 45, result

    def test_exceptions(self):
        f = mod.get_function('raise')
        try:
            result = interp.run(f)
        except interp.UncaughtException as e:
            exc, = e.args
            assert isinstance(exc, TypeError), exc
        else:
            assert False, result


if __name__ == '__main__':
    unittest.main()