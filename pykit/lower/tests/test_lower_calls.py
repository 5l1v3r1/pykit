# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import
import textwrap
from pykit.tests import *
from pykit.lower import lower_calls

class TestCallLowering(SourceTestCase):

    source = textwrap.dedent("""
    #include <pykit_ir.h>

    extern float external(float);

    float testfunc(float a) {
        return (float) call(external, list(a));
    }
    """)

    def test_badval(self):
        call = findop(self.entry, 'call')
        call.add_metadata({'exc.badval': Const(0)})
        self.eq(opcodes(self.f), ['call', 'convert', 'ret'])
        lower_calls.run(self.f, self.env)
        self.eq(opcodes(self.f), ['call', 'check_error', 'convert', 'ret'])

    def test_raise(self):
        call = findop(self.entry, 'call')
        call.add_metadata({'exc.badval': Const(0)})
        call.add_metadata({'exc.raise': Const(RuntimeError, types.Exception)})
        self.eq(opcodes(self.f), ['call', 'convert', 'ret'])
        lower_calls.run(self.f, self.env)
        self.eq(opcodes(self.f), ['call', 'convert', 'eq', 'cbranch',
                                  'new_exc', 'exc_throw', 'convert', 'ret'])

        self.eq(findop(self.f, 'exc_throw').args[0], findop(self.f, 'new_exc'))
        self.eq(findop(self.f, 'new_exc').args[0].const, RuntimeError)


if __name__ == '__main__':
    TestCallLowering('test_badval').debug()
    unittest.main()