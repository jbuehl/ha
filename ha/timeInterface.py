from ha.HAClasses import *
import time

class TimeInterface(HAInterface):
    def __init__(self, name):
        HAInterface.__init__(self, name, None)

    def read(self, addr=None):
        if addr:
            if addr == "daytime":
                return normalState(sunIsUp(todaysDate()[0], latLong))
            else:
                return time.strftime(addr).lstrip("0")
        else:
            return time.asctime()

