from .config import *
from .logging import *

# log a debug message conditioned on a specified global variable
def debug(*args):
    try:
        if debugEnable:   # global debug flag enables debugging
            if globals()[args[0]]:  # only log if the specified debug variable is True
                log(*args[1:])
    except KeyError:
        pass

# log a stack trace conditioned on a specified global variable
def debugTraceback(debugType, debugName):
    try:
        if debugEnable:   # global debug flag enables debugging
            if globals()[debugType]:
                s = inspect.stack()
                for f in s:
                    log(debugName, f[1], f[2], f[3], f[4])
    except KeyError:
        pass

