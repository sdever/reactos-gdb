import gdb
from lib.utils import get_type, pvoid, FunctionWrapper

def find_object_by_handle(handle_table, handle):
    HANDLE = get_type("HANDLE")
    EXHANDLE = get_type("EXHANDLE")
    PHANDLE_TABLE = get_type("HANDLE_TABLE").pointer()
    PHANDLE_TABLE_ENTRY = get_type("HANDLE_TABLE_ENTRY").pointer()

    exhandle = handle.cast(HANDLE).cast(EXHANDLE)
    tbl = handle_table.reinterpret_cast(PHANDLE_TABLE)
    print(tbl["NextHandleNeedingPool"])
    print(exhandle["Value"])
    if exhandle["Value"] >= tbl["NextHandleNeedingPool"]:
        print("Invalid handle given")
        return -1
    level = (tbl["TableCode"] & 3)
    pointer = gdb.Value(tbl["TableCode"] & ~3).cast(pvoid.pointer())
    if level == 2:
        pointer = pointer[exhandle["HighIndex"]]
        array = pointer[exhandle["MidIndex"]].cast(PHANDLE_TABLE_ENTRY)
        entry = array[exhandle["LowIndex"]]
    if level == 1:
        array = pointer[exhandle["MidIndex"]].cast(PHANDLE_TABLE_ENTRY)
        entry = pointer[exhandle["LowIndex"]]
    if level == 0:
        print(exhandle["LowIndex"])
        entry = pointer.cast(PHANDLE_TABLE_ENTRY)[exhandle["LowIndex"]]
    return gdb.Value(int(entry["Object"]) & (~7)).cast(get_type("OBJECT_HEADER").pointer())

FunctionWrapper("obentry", find_object_by_handle)