import gdb
from lib.utils import FunctionWrapper, get_type, offsetof, CommandWrapper

#region Utilities functions to manipulate VAD tree
def find_vad_by_addr(addr, value):
    """
    Finds the VAD object for a given address.
    @param addr The vad root to start searching from
    @param value The value to find
    """

    PMMVAD = get_type("struct _MMVAD_LONG").pointer()
    vadnode = gdb.Value(int(addr)).cast(PMMVAD)

    if int(vadnode["u1"]["Parent"]) != int(addr):
        # We are not a MM_AVL_TABLE root
        to_check = value // 4096
        starting = int(vadnode["StartingVpn"])
        ending = int(vadnode["StartingVpn"])

        if  starting >= to_check and ending <= to_check:
            return vadnode
        
        # Explore children
        if to_check < starting:
            return None if int(vadnode["LeftChild"]) == 0 else find_vad_by_addr(vadnode["LeftChild"], value)
        else:
            return None if int(vadnode["RightChild"]) == 0 else find_vad_by_addr(vadnode["RightChild"], value)
    else:
        # We are a MM_AVL_TABLE root, so just lookup childs
        ret = None
        if int(vadnode["LeftChild"]) != 0:
            ret = find_vad_by_addr(vadnode["LeftChild"], value)
        if ret:
            return ret
        if int(vadnode["RightChild"]) != 0:
            ret = find_vad_by_addr(vadnode["RightChild"], value)
        return ret

def is_arm3_vad(mmvad):
    """
    Check if the VAD is managed by ARM3 or the old ReactOS memory manager
    @param mmvad gdb.Value representing the VAD
    @return True if it belongs to ARM3, False otherwise
    """

    return (True if mmvad.dereference()["u"]["VadFlags"]["Spare"] == 0 else False)

def get_vad_section_file(vad):
    """
    Returns the file backing the section VAD if any
    @param vad The vad to lookup
    @return The name of the file if any, empty string otherwise
    """

    if is_arm3_vad(vad):
        # ARM3 doesn't support file-backed sections yet ?
        return ""
    else:
        memarea = vad.cast(get_type("MEMORY_AREA").pointer())
        if (memarea["Type"] & 1) == 0:
            return ""
        ros_section = memarea["Data"]["SectionData"]["Section"]
        if ros_section.dereference()["FileObject"] != 0:
            return ros_section["FileObject"]["FileName"]["Buffer"].string()
    return ""
#endregion

#region Handler for vadtree command
def print_vads(arg, from_tty=False):
    if arg == "":
        print("VAD address required")
        return
    try:
        addr = gdb.parse_and_eval(arg)
        addr = gdb.Value(int(addr)).cast(get_type("MM_AVL_TABLE").pointer())
    except gdb.error:
        print("Invalid address given")
        return
    fmt = "".join(["%-12s", "%-7s", "%-12s", "%-12s", "%-15s","%-50s"])
    d =  fmt % (
        "VAD",
        "Depth",
        "Start VPN",
        "End VPN",
        "Mem type",
        "Filename")
    print(d)
    print("-"*len(d))
    if addr["BalancedRoot"]["LeftChild"]:
        print_vad_tree(0, addr["BalancedRoot"]["LeftChild"])
    if addr["BalancedRoot"]["RightChild"]:
        print_vad_tree(0, addr["BalancedRoot"]["RightChild"])

# Print the VAD Tree starting from the VAD
def print_vad_tree(depth, addr):
    PMMVAD = get_type("struct _MMVAD_LONG").pointer()
    vadroot = gdb.Value(int(addr)).cast(PMMVAD)

    if vadroot["LeftChild"] != 0:
        print_vad_tree(depth+1, vadroot.dereference()["LeftChild"])

    vad_type = "ARM3 VAD" if is_arm3_vad(vadroot) else "Ros VAD"
    filename = get_vad_section_file(vadroot)
    fmt = "".join(["0x%-10x", "%-7d", "0x%-10x", "0x%-10x", "%-10s", "%-15s", "%-50s"])                
    print(fmt % 
        (
            int(vadroot),
            depth,
            vadroot["StartingVpn"] * 4096,
            vadroot["EndingVpn"] * 4096,
            vad_type,
            filename
        )
    )

    # Explore right child
    if vadroot["RightChild"] != 0:
        print_vad_tree(depth+1, vadroot["RightChild"])

CommandWrapper("vadtree", print_vads)
#endregion

#region Handler for vadinfo command
def print_vad_header(vad):
    print("Vad 0x%x" % int(vad))
    print(" - Parent VAD: 0x%x" % vad["u1"]["Parent"])
    print(" - Left child: 0x%x" % vad["LeftChild"])
    print(" - Left right: 0x%x" % vad["RightChild"])

def print_ros_vad(vad):
    print("VAD backed by ReactOS old memory manager")
    memarea = vad.cast(gdb.lookup_type("MEMORY_AREA").pointer())
    type = memarea["Type"]
    if type == 15:
        print(" [!] Found ARM3 section !")
        return
    if (type & 1) == 1:
        print(" - Section object: (PROS_SECTION_OBJECT)0x%x" % memarea["Data"]["SectionData"]["Section"])
        sect = memarea["Data"]["SectionData"]["Section"]
        fileobj = sect["FileObject"]
        if fileobj == 0:
            return
        print(" - File Object: (PFILE_OBJECT)0x%x" % sect["FileObject"])
        print(" - File name: %s" % get_vad_section_file(vad))

def print_arm3_vad(vad):
    print("ARM3 managed VAD")
    if vad["ControlArea"] == 0:
        print(" - VMalloc")
    else:
        print(" - ARM3 Section")

def vadinfo(arg, is_tty=False):
    if arg == "":
        print("VAD address required")
        return
    addr = gdb.parse_and_eval(arg)
    PMMVAD = gdb.lookup_type("struct _MMVAD_LONG").pointer()
    vad = gdb.Value(addr).cast(PMMVAD)
    print_vad_header(vad)
    if(int(vad["u1"]["Parent"]) == addr):
        print("This is a VAD_ROOT")
        return
    print(" - Virtual address start: 0x%x" % (vad["StartingVpn"] << 12))
    print(" - Virtual address end: 0x%x" % (vad["EndingVpn"] << 12))
    if is_arm3_vad(vad):
        print_arm3_vad(vad)
    else:
        print_ros_vad(vad)

CommandWrapper("vadinfo", vadinfo)
#endregion