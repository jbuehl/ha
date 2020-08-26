# Logging functions

from __future__ import print_function
import syslog
import os
import time
import threading
import traceback
from .environment import *

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
        print(timeStamp("%b %d %H:%M:%S")+" "+message)

# thread object that logs a stack trace if there is an uncaught exception
class LogThread(threading.Thread):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.runTarget = self.run
        self.run = self.logThread

    def logThread(self):
        try:
            self.runTarget()
        except Exception as ex:
            tb = traceback.format_exception(None, ex, ex.__traceback__)
            log("thread", threading.currentThread().name+":")
            for t in tb:
                log(t)
