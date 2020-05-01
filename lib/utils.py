import gdb

# Utility functions
def FunctionWrapper(command, fn):
    """
    Wraps stuff needed to expose a gdb function
    @param command The name of the function in GDB
    @param fn The function to invoke
    """
    class Temp(gdb.Function):
        def __init__(self):
            super(Temp, self).__init__(command)

        def invoke(self, *args):
            return fn(*args)
    Temp()

def CommandWrapper(command, fn):
    """
    Wraps stuff needed to expose a gdb command
    @param command The name of the command in GDB
    @param fn The command to invoke
    """
    class Temp(gdb.Command):
        def __init__(self):
            super(Temp, self).__init__(command, gdb.COMMAND_USER)
        
        def invoke(self, *args, **kwargs):
            fn(*args, **kwargs)
    Temp()

pvoid = gdb.lookup_type('void').pointer()

def containing_record(ptr, type, attr):
    """
    Gets the original type from a pointer to a member
    @arg ptr: a gdb.Value representing the pointer to the attribute
    @arg type: A gdb.Type which corresponds to the base type
    @arg attr: Name of the attribute of the pointer
    @return: a gdb.Value corresponding to the pointer
    """
    offset = type[attr].bitpos // 8
    return gdb.Value(int(ptr) - offset).cast(type.pointer())

# Helper that tries to load symbols when invoking command
def get_type(tn):
    try:
        return gdb.lookup_type(tn)
    except Exception:
        pass
    gdb.execute("sharedlibrary")
    return gdb.lookup_type(tn)

def get_symbol_value(sn):
    try:
        return gdb.get_symbol(sn).value()
    except Exception:
        pass
    gdb.execute("sharedlibrary")
    return gdb.get_symbol(sn).value()