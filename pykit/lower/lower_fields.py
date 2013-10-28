# -*- coding: utf-8 -*-

"""
Rewrite field accesses on pointers.
"""

from pykit.ir import Builder, Op, OpBuilder

def lower_fields(func, env):
    b = Builder(func)
    opbuilder = OpBuilder()

    for op in func.ops:
        if op.opcode not in ("getfield", "setfield"):
            continue

        if op.args[0].type.is_pointer:
            b.position_before(op)

            # Load the pointer and update the argument
            p = op.args[0]
            load = b.load(p)
            args = [load] + op.args[1:]
            op.set_args(args)

            if op.opcode == "setfield":
                # Write back result
                b.position_after(op)
                op.type = load.type
                b.store(op, p)

        if op.opcode == "getfield":
            struct, attr = op.args
            newop = opbuilder.extractfield(op.type, struct, attr,
                                           result=op.result)
        else:
            struct, attr, value = op.args
            newop = opbuilder.insertfield(op.type, struct, attr, value,
                                          result=op.result)

        op.replace(newop)


run = lower_fields