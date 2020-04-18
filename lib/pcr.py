from lib.utils import get_type, FunctionWrapper
import gdb

# Grab some info from the PCR
def get_pcr():
    KPCR = get_type("KPCR")
    return gdb.Value(0xFFDFF000).cast(KPCR.pointer())

def get_running_thread():
    kthread = get_type("KTHREAD").pointer()
    pcr = get_pcr()
    thrd = pcr["Prcb"].dereference()["CurrentThread"].cast(kthread)
    return thrd

def get_running_process():
    thrd = get_running_thread()
    return thrd["Process"].cast(get_type("EPROCESS").pointer())

# GDB functions
"""
getpcr(): Gets a pointer to the first PCR
"""
FunctionWrapper("getpcr", get_pcr)

"""
curthread(): Print the current thread in the first PCR
"""
FunctionWrapper("curthread", get_running_thread)

"""
curproc(): show the current executed process (not the one attached !)
The current executed thread is stored in the PCR
"""
FunctionWrapper("curproc", get_running_process)