# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
import textwrap

from pykit.analysis import cfa
from pykit.parsing import from_c
from pykit.optimizations import sccp
from pykit.ir import verify, Const


class TestVector(unittest.TestCase):

    def test_vector(self):
        simple = textwrap.dedent("""
        #include <pykit_ir.h>

        Vector<UInt32, 4> f() {
            Vector<UInt32, 4> x, y;

            x = 2; // TODO: fill vector?
            y = 3;

            return x + y;
        }
        """)
        mod = from_c(simple)
        f = mod.get_function("f")
        cfa.run(f)
        sccp.run(f)
        verify(f)

        # TODO: what ops should I expect out?
        ops = list(f.ops)
        assert len(list(f.ops)) == 1
        [op] = ops
        assert op.opcode == 'ret'
        assert isinstance(op.args[0], Const)
        self.assertEqual(op.args[0].const, 5) # TODO: construct vector to compare?
