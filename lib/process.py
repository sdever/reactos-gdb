#!/usr/bin/python
"""
Handle ReactOS processes and threads support (mostly processes, since gdb
already returns a lot of information on threads)
"""
current_thread = None
current_process = None

from lib.utils import get_type, containing_record, pvoid, FunctionWrapper, \
    CommandWrapper, get_symbol_value
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
        ps = containing_record(next, EPROCESS, "ActiveProcessLinks")
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
        ps = get_current_process()
    if not ps:
        return -1
    vad_root = gdb.Value(int(ps) + (EPROCESS["VadRoot"].bitpos // 8))
    ret = find_vad_by_addr(vad_root, addr)
    if not ret:
        return -1
    return ret

FunctionWrapper("psaddr", get_vad_from_addr)

# Dedicated command to kill a process
def kill_process(arg, from_tty=False):
    try:
        ps = gdb.parse_and_eval(arg)
    except Exception:
        print("Invalid expression given")
        return
    gdb.execute("set ExpDebuggerProcessKill = 0x%x" % ps)
    gdb.execute("set ExpDebuggerWork = 1")
    gdb.execute("c")

def get_current_process(*args):
    """
    Get the current process being run by kdgdb. It differs from the
    current thread in the PCR if kdbg attaches to another thread.
    It makes more sense for curproc to return it instead of the PCR
    one
    """
    global current_process
    EPROCESS = get_type("EPROCESS")
    KPROCESS = get_type("KPROCESS")
    ETHREAD = get_type("ETHREAD")
    KTHREAD = get_type("KTHREAD")
    tid = gdb.parse_and_eval("gdb_dbg_tid")
    if current_thread and current_thread["Cid"]["UniqueThread"] == (tid - 1):
        return current_process
    
    def search_fun(ps):
        global current_process, current_thread
        pcb = gdb.Value(int(ps) + \
            (EPROCESS["Pcb"].bitpos // 8)).cast(KPROCESS.pointer())
        th_head = gdb.Value(int(pcb) + \
            (KPROCESS["ThreadListHead"].bitpos // 8))
        th_head = th_head.cast(get_type("LIST_ENTRY").pointer())
        next = th_head['Flink']
        while int(next) != int(th_head):
            th = containing_record(next, KTHREAD, "ThreadListEntry")
            eth = th.cast(ETHREAD.pointer())
            if eth["Cid"]["UniqueThread"] == (tid - 1):
                current_thread = eth
                current_process = ps
                return ps
            next = next["Flink"]
        return False
    return ProcessWalk(search_fun)
    

CommandWrapper("pskill", kill_process)
FunctionWrapper("dbgproc", get_current_process)