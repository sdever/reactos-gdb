#!/usr/bin/python
import gdb
from lib.utils import CommandWrapper
# Gflags constants come from https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/-gflag
gflags = {
    "soe": 0x00000001,
    "sls": 0x00000002,
    "dic": 0x00000004,
    "shg": 0x00000008,
    "htc": 0x00000010,
    "hfc": 0x00000020,
    "hpc": 0x00000040,
    "hvc": 0x00000080,
    "ptc": 0x00000100,
    "pfc": 0x00000200,
    "ptg": 0x00000400,
    "htg": 0x00000800,
    "ust": 0x00001000,
    "kst": 0x00002000,
    "otl": 0x00004000,
    "htd": 0x00008000,
    "d32": 0x00020000,
    "ksl": 0x00040000,
    "dps": 0x00080000,
    "scb": 0x00100000,
    "dhc": 0x00200000,
    "ece": 0x00400000,
    "eel": 0x00800000,
    "eot": 0x01000000,
    "hpa": 0x02000000,
    "dwl": 0x04000000,
    "ddp": 0x08000000,
    "sue": 0x20000000,
    "dpd": 0x80000000
}

def get_static_symbol(name):
    """"
    Helper who tries to reload symbols if getting symbol fails
    """
    try:
        return gdb.lookup_global_symbol(name)
    except Exception:
        gdb.execute("sharedlibrary")
        return gdb.lookup_global_symbol(name)


def print_flags():
    out = []
    flagval = int(get_static_symbol("NtGlobalFlag").value())
    for flag in gflags:
        if (flagval & gflags[flag]) == gflags[flag]:
            out.append(flag)
    if len(out) > 0:
        print("Enabled flags: %s" % ", ".join(out))
    else:
        print("No enabled flags")

def set_gflags(arg, from_tty=False):
    nt_flags = get_static_symbol("NtGlobalFlag")
    if arg == "":
        return print_flags()
    flag = arg
    operation = flag[0]
    if operation not in ["+", "-"]:
        operation = "+"
    else:
        flag = flag[1:]
    if flag not in gflags:
        print("Unknown flag %s" % flag[1:])
    
    # Add a flag
    if operation == "+":
        # Enable flag
        gdb.execute("set NtGlobalFlag = 0x%x" % (nt_flags.value() | gflags[flag]))
        return
    # Remove a flag
    if operation == "-":
        # Disable flag
        value = ~gflags[flag]
        gdb.execute("set NtGlobalFlag = 0x%x" % (nt_flags.value() & value))
        return
    print("Usage: gflags [+/-flag]")


CommandWrapper("gflags", set_gflags)