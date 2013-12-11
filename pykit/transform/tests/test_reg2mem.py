# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
import textwrap

from pykit.analysis import cfa
from pykit.parsing import from_c
from pykit.transform import reg2mem
from pykit.ir import opcodes, findallops, verify, interp

class TestReg2mem(unittest.TestCase):

    def test_swap(self):
        simple = textwrap.dedent("""
        #include <pykit_ir.h>

        int f(int i) {
            int x = 1;
            int y = 2;
            int tmp;
            while (i > 0) {
                tmp = x;
                x = y;
                y = tmp;
                i = i - 1;
            }
            return x;
        }
        """)
        mod = from_c(simple)
        func = mod.get_function("f")
        cfa.run(func)

        verify(func)
        ssa_result1 = interp.run(func, args=[1])
        ssa_result2 = interp.run(func, args=[2])

        reg2mem.reg2mem(func)
        verify(func)

        stack_result1 = interp.run(func, args=[1])
        stack_result2 = interp.run(func, args=[2])

        self.assertEqual(ssa_result1, stack_result1)
        self.assertEqual(ssa_result2, stack_result2)

    def test_swap_loop(self):
        simple = textwrap.dedent("""
        #include <pykit_ir.h>

        int f(int i, int j) {
            int x = 1;
            int y = 2;
            int tmp;
            while (i > 0) {
                while (j > 0) {
                    tmp = x;
                    x = y;
                    y = tmp;
                    j = j - 1;
                }
                i = i - 1;
            }
            return x;
        }
        """)
        mod = from_c(simple)
        func = mod.get_function("f")
        cfa.run(func)

        verify(func)

        ssa_results = []
        for i in range(10):
            for j in range(10):
                ssa_result = interp.run(func, args=[i, j])
                ssa_results.append(ssa_result)

        #print(func)
        reg2mem.reg2mem(func)
        verify(func)
        #print(func)

        stack_results = []
        for i in range(10):
            for j in range(10):
                stack_result = interp.run(func, args=[i, j])
                stack_results.append(stack_result)


if __name__ == '__main__':
    unittest.main()