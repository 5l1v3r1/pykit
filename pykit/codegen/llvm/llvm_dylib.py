from llvm.ee import dylib_add_symbol

DYLIB = {}

def install(symbol, address):
    if symbol in DYLIB:
        raise KeyError("Duplicated symbol '%s'" % symbol)
    DYLIB[symbol] = address
    dylib_add_symbol(symbol, address)

def has(symbol):
    return symbol in DYLIB

def uninstall(symbol):
    del DYLIB[symbol]
    dylib_add_symbol(symbol, 0)  # insert poison value
