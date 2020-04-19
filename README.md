# Extensions to debug ReactOS from GDB
This set of gdb extensions aim to ease ReactOS debugging by providing easier access to internal kernel structures.
This is experimental work-in-progress, only works with i686 architecture at the moment.

## Quick start
`git clone` the repository somewhere in your computer.

Type `source /where/you/downloaded/rosdbg.py` in your gdb debugging session. To setup remote debugging of ReactOS with GDB, please see https://reactos.org/wiki/GDB

## Implemented commands
 - `pslist`: Prints the list of processes, without the PsInitialProcess
 - `vadtree`: Dumps the VAD tree of a VAD root.
 - `vadinfo`: Prints information about a specific VAD
 - `gflags`: Prints currently set gflags
 - `gflags [+|-]gflag` Sets or disable a gflag

## Implemented functions
 - `$getpcr()`: Returns a pointer to the first PCR of a process
 - `$curproc()`: Returns a pointer to the current _EPROCESS to the current thread in the PCR
 - `$curthread()`: Returns the current _ETHREAD in the PCR
 - `$psaddr(pid, addr)`: Returns a pointer to the VAD describing the virtual address for a given PID.
 - `$psaddr(addr)`: Return a pointer to the VAD describind the virtual address for the current process