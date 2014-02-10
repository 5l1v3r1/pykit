#===------------------------------------------------------------------===
# Constant Folding
#===------------------------------------------------------------------===

def check_consts(cells, args):
    """Check whether all IR arguments are constants accordign to `cells`"""
    return all(isconst(cells[arg]) for arg in args)


def load_consts(cells, args):
    """Load the constants from `cells`"""
    return [cells[arg].const for arg in args]


def folding(f):
    """
    Define a function that folds constants:

        @folding
        def op_add(self, a, b):
            return a + b
    """
    def wrapper(self, op, cells):
        if check_consts(cells, op.args):
            return f(self, *load_consts(cells, op.args))
        return None
    return wrapper


class ConstantFolder(object):
    """Fold constants!"""

    def fold(self, op, cells):
        m = getattr(self, 'op_' + op.opcode, None)
        result = None
        if m is not None:
            result = m(op, cells)
            if (result is not None and isconst(result) and not
                    isinstance(result, Const)):
                result = Const(result, op.type)
                cells[result] = result

        if result is None:
            result = bottom # Undetermined value

        cells[op] = result
        return result

    def op_phi(self, op, cells):
        blocks, args = op.args
        return reduce(meet, [unwrap(cells[arg]) for arg in args])

    def op_convert(self, op, cells):
        return cells[op.args[0]]

    # Binary

    @folding
    def op_add(self, a, b):
        return a + b

    @folding
    def op_mul(self, a, b):
        return a * b

    @folding
    def op_sub(self, a, b):
        return a - b

    @folding
    def op_div(self, a, b):
        return a / b

    @folding
    def op_mod(self, a, b):
        return a % b

    @folding
    def op_lshift(self, a, b):
        return a << b

    @folding
    def op_rshift(self, a, b):
        return a >> b

    @folding
    def op_bitand(self, a, b):
        return a & b

    @folding
    def op_bitor(self, a, b):
        return a | b

    @folding
    def op_bitxor(self, a, b):
        return a ^ b

    @folding
    def op_eq(self, a, b):
        return a == b

    @folding
    def op_ne(self, a, b):
        return a != b

    @folding
    def op_lt(self, a, b):
        return a < b

    @folding
    def op_le(self, a, b):
        return a <= b

    @folding
    def op_gt(self, a, b):
        return a > b

    @folding
    def op_ge(self, a, b):
        return a >= b

    # Unary

    @folding
    def op_invert(self, x):
        return ~x

    # vv are these even used ? vv #

    @folding
    def op_not_(self, x):
        return not x

    @folding
    def op_uadd(self, x):
        return +x

    @folding
    def op_usub(self, x):
        return -x

    # ^^ are these even used ? ^^ #