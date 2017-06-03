from config import *
from logging import *

# log a debug message conditioned on a specified global variable
def debug(*args):
    try:
        if debugEnable:   # global debug flag enables debugging
            if globals()[args[0]]:  # only log if the specified debug variable is True
                log(*args[1:])
    except:
        pass


