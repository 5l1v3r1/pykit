# -*- coding: utf-8 -*-

"""
C codegen utilities.
"""

from __future__ import print_function, division, absolute_import

from pykit.utils import make_temper
from . import c_codegen
from .. import codegen

name = "c"

def install(env, opt=3, temper=make_temper()):
    """Install C code generator in environment"""

    # -------------------------------------------------
    # Codegen passes

    env["pipeline.codegen"].extend([
        "passes.llvm.postpasses",
        "passes.llvm.ctypes",
    ])

    env["passes.codegen"] = codegen
    env["codegen.impl"] = c_codegen


def verify(func, env):
    """Verify C code"""

def optimize(func, env):
    """Optimize C code"""

def get_ctypes(func, env):
    raise NotImplementedError

def execute(func, env, *args):
    """Execute C function with the given arguments"""
    cfunc = get_ctypes(func, env)
    assert len(func.args) == len(args)
    return cfunc(*args)