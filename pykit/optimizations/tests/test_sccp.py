# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
import textwrap

from pykit.analysis import cfa
from pykit.parsing import from_c
from pykit.optimizations import sccp
from pykit.ir import verify, Const


class TestSparseConditionalConstantPropagation(unittest.TestCase):

    def test_sccp(self):
        simple = textwrap.dedent("""
        #include <pykit_ir.h>

        Int32 f(Int32 i) {
            Int32 x, y, z;

            x = 2;
            y = 3;
            z = 4;

            if (x < y)
                x = y;
            else
                x = i;

            return x + z;
        }
        """)
        mod = from_c(simple)
        f = mod.get_function("f")
        cfa.run(f)
        sccp.run(f)
        verify(f)

        ops = list(f.ops)
        assert len(list(f.ops)) == 1
        [op] = ops
        assert op.opcode == 'ret'
        assert isinstance(op.args[0], Const)
        self.assertEqual(op.args[0].const, 7)

    def test_sccp_endless_loop(self):
        simple = textwrap.dedent("""
        #include <pykit_ir.h>

        Int32 f(Int32 i) {
            Int32 x, y, z;

            x = 2;
            y = 3;
            z = 4;

            while (x < y) {
                if (x < y) {
                    x = 2;
                }
            }

            return x + z;
        }
        """)
        mod = from_c(simple)
        f = mod.get_function("f")
        cfa.run(f)
        sccp.run(f)
        verify(f)

        assert len(f.blocks) == 2
        start, loop = f.blocks
        assert start.terminator.opcode == 'jump'
        assert start.terminator.args[0] == loop
        assert loop.terminator.opcode == 'jump'
        assert loop.terminator.args[0] == loop

    def test_sccp_dead_loop(self):
        simple = textwrap.dedent("""
        #include <pykit_ir.h>

        Int32 f(Int32 i) {
            Int32 x, y, z;

            x = 2;
            y = 3;
            z = 4;

            while (y < x) {
                if (y < x) {
                    x = 1;
                    x = x + 1;
                    y = x - z;
                }
            }

            return x + z;
        }
        """)
        mod = from_c(simple)
        f = mod.get_function("f")
        cfa.run(f)
        sccp.run(f)
        verify(f)

        verify(f)
        ops = list(f.ops)
        assert len(list(f.ops)) == 1
        [op] = ops
        assert op.opcode == 'ret'
        assert isinstance(op.args[0], Const)
        self.assertEqual(op.args[0].const, 6)

    def test_ops(self):
        source = textwrap.dedent("""
        #include <pykit_ir.h>

        Int32 f(Int32 i) {
            Int32 x;

            x = 2;

            if (x < 3)
                x = x + 1;
            if (x <= 3)
                x = x + 1;
            if (x >= 3)
                x = x + 1;
            if (x >= 3)
                x = x + 1;
            if (x > 3)
                x = x + 1;

            return x;
        }
        """)

        mod = from_c(source)
        f = mod.get_function("f")
        remove_convert(f)
        cfa.run(f)
        sccp.run(f)
        verify(f)

        # print(f)

        # ops = list(f.ops)
        # assert len(list(f.ops)) == 1
        # [op] = ops
        # assert op.opcode == 'ret'
        # assert isinstance(op.args[0], Const)
        # self.assertEqual(op.args[0].const, 7)


def remove_convert(func):
    """Remove dummy conversion ops"""
    for op in func.ops:
        if op.opcode == 'convert' and op.type == op.args[0].type:
            op.replace_uses(op.args[0])
            op.delete()

if __name__ == '__main__':
    unittest.main()