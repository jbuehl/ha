from ha.HAClasses import *
import time
import datetime
import pytz

class GpsTimeInterface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)

    def read(self, addr=None):
        # read the gps time from the file
        timestamp = self.interface.read("Time")
        tz = self.interface.read("TimeZone")
        if not tz:
            tz = "UTC"
        fmt = "%Y-%m-%d %H:%M:%S"
        # convert to local TZ
        print timestamp, tz
        now = datetime.datetime(*time.strptime(timestamp, fmt)[0:6], tzinfo=pytz.utc).astimezone(pytz.timezone(tz))
        if addr:
            if addr == "daylight":
                return normalState(sunIsUp(todaysDate()[0], latLong))
            elif addr == "sunrise":
                return sunrise(todaysDate()[0], latLong).strftime("%I:%M %p").lstrip("0")
            elif addr == "sunset":
                return sunset(todaysDate()[0], latLong).strftime("%I:%M %p").lstrip("0")
            else:
                return now.strftime(addr)
        else:
            return now.strftime(fmt)

