from ha.HAClasses import *
import time
import os
import datetime

class TimeInterface(HAInterface):
    def __init__(self, name, tzOffset=0):
        HAInterface.__init__(self, name, None)
        self.tzOffset = tzOffset

    def read(self, addr=None):
        now = datetime.datetime.now() + datetime.timedelta(hours=self.tzOffset)
        if addr:
            if addr == "daylight":
                return normalState(sunIsUp(todaysDate()[0], latLong))
            elif addr == "sunrise":
                return sunrise(todaysDate()[0], latLong).strftime("%I:%M %p").lstrip("0")
            elif addr == "sunset":
                return sunset(todaysDate()[0], latLong).strftime("%I:%M %p").lstrip("0")
            else:
                return time.strftime(addr, now.timetuple()).lstrip("0")
        else:
            return time.asctime()

