from ha.HAClasses import *
import time

class TimeInterface(HAInterface):
    def __init__(self, name):
        HAInterface.__init__(self, name, None)

    def read(self, addr=None):
        if addr:
            if addr == "daylight":
                return normalState(sunIsUp(todaysDate()[0], latLong))
            elif addr == "sunrise":
                return sunrise(todaysDate()[0], latLong).strftime("%I:%M %p").lstrip("0")
            elif addr == "sunset":
                return sunset(todaysDate()[0], latLong).strftime("%I:%M %p").lstrip("0")
            else:
                return time.strftime(addr).lstrip("0")
        else:
            return time.asctime()

