# Logging and debug functions

import syslog
import os
from environment import *

# standard timestamp
def timeStamp(fmt):
    return time.strftime(fmt, time.localtime())
    
# log a message to syslog or stdout
def log(*args):
    message = args[0]+" "   # first argument is the object doing the logging
    for arg in args[1:]:
        message += arg.__str__()+" "
    if sysLogging:
        syslog.syslog(message)
    else:
        print timeStamp("%b %d %H:%M:%S")+" "+message

# log a debug message conditioned on a specified global variable
def debug(*args):
    try:
        if debugEnable:   # global debug flag enables debugging
            if globals()[args[0]]:  # only log if the specified debug variable is True
                log(*args[1:])
    except:
        pass

# log a data point
def logData(name, value):
    try:
        if debugFileName != "":
            with open(dataLogDir+timestamp("%Y%m%d-")+dataLogFileName+".csv", "a") as dataLogFile:
                dataLogFile.write(timestamp("%Y %m %d %H:%M:%S")+","+name+","+value)
    except:
        pass

