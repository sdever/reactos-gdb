#!/usr/bin/python
"""
Handle ReactOS processes and threads support (mostly processes, since gdb
already returns a lot of information on threads)
"""

from lib.utils import get_type, offsetof, pvoid, FunctionWrapper, \
    CommandWrapper
from lib.memory.vad import find_vad_by_addr, get_vad_section_file
from lib.pcr import get_running_process
import gdb

"""
Walks through a process and execute a function on each iteration
Returns False to continue loop
"""
def ProcessWalk(fn):
    EPROCESS = get_type("EPROCESS")
    if not EPROCESS:
        return
    z = gdb.parse_and_eval("&PsActiveProcessHead")
    head_ref = z.cast(pvoid)
    next = z["Flink"]
    while int(next) != int(head_ref):
        ps = offsetof(next, EPROCESS, "ActiveProcessLinks")
        ret = fn(ps)
        if not ret:
            next = next["Flink"]
        else:
            return ret

"""
Find a process object by its PID
"""

def find_by_pid(pid):
    def l(s):
        if (int(s["UniqueProcessId"]) == pid):
            return s
        return False
    return ProcessWalk(l)

## GDB commands export


class GetPsList(gdb.Command):
    """
    pslist command
    """
    def __init__(self):
        super(GetPsList, self).__init__("pslist", gdb.COMMAND_USER)
    
    def ps_print(self, ps):
        EPROCESS = get_type("EPROCESS")
        vad_root = gdb.Value(int(ps) + (EPROCESS["VadRoot"].bitpos // 8))
        linefmt = "".join(["0x%-13x", "%-8d" "%-32s", "0x%08x   ", "0x%08x "])
        print(linefmt % 
            (
                ps,
                ps["UniqueProcessId"],
                ps["ImageFileName"].string(),
                ps["SectionObject"],
                vad_root
            ))

    def invoke(self, arg, from_tty):
        linefmt = "".join(["%-15s", "%-8s", "%-32s", "%-14s", "%-10s"])
        s = linefmt % ("EPROCESS", "PID", "Image", "Section Obj", "VAD root")
        print(s)
        print("-"*len(s))
        ProcessWalk(self.ps_print)
           
GetPsList()

def get_vad_from_addr(*args):
    if len(args) not in [1,2]:
        print("Usage: $psaddr(<pid>,<vaddr>)")
        return 0
    EPROCESS = get_type("EPROCESS")
    if len(args) == 2:
        pid = int(args[0])
        addr = int(args[1])
        ps = find_by_pid(pid)
    else:
        addr = int(args[0])
        ps = get_running_process()
    if not ps:
        return -1
    vad_root = gdb.Value(int(ps) + (EPROCESS["VadRoot"].bitpos // 8))
    ret = find_vad_by_addr(vad_root, addr)
    if not ret:
        return -1
    return ret

FunctionWrapper("psaddr", get_vad_from_addr)