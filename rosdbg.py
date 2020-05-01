#!/usr/bin/python
import os
import sys
import importlib

def reload(x):
    # Could break in ancient versions of python, remove it if not debug
    if x in sys.modules:
        del sys.modules[x]
    importlib.__import__(x)

# point to absolute path of rosdbg.py
THISFILE = os.path.abspath(os.path.expanduser(__file__))
if os.path.islink(THISFILE):
    PEDAFILE = os.readlink(THISFILE)
sys.path.insert(0, os.path.dirname(THISFILE))

reload("lib.utils")
reload("lib.memory.vad")
reload("lib.process")
reload("lib.pcr")
reload("lib.obmgr")
reload("lib.gflags")