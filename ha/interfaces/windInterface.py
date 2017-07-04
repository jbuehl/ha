# Calculate wind speed and direction using the Peet Ultimeter Pro Anemometer

import time
import threading
from ha import *
from ha.interfaces.gpioInterface import *

# global variables
startTime = time.time() # speed contact closure time
speedTime = 0.0         # delta tSpeed
dirTime = 0.0           # delta tDir

# anemometer contact closure interrupt routine
def speedInterrupt(sensor, state):
    global startTime, speedTime, dirTime
    curTime = time.time()
    if state == 1:
        speedTime = curTime - startTime
        startTime = curTime

# wind vane contact closure interrupt routine        
def dirInterrupt(sensor, state):
    global startTime, speedTime, dirTime
    curTime = time.time()
    if state == 1:
        dirTime = curTime - startTime

class WindInterface(Interface):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface, anemometer, windVane, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.anemometer = anemometer    # anemometer contact closure sensor
        self.anemometer.interrupt = speedInterrupt
        self.windVane = windVane        # wind vane contact closure sensor
        self.windVane.interrupt = dirInterrupt
        debug("debugWind", "anemometer:", self.anemometer.name, "windVane:", self.windVane.name)

    def read(self, addr):
        if addr == "speed":
            # calculate revolutions per second
            try:
                rps = 1.0 / speedTime
            except ZeroDivisionError:
                rps = 0.0
            # approximate the wind speed in mph
            if rps < .010:
                mph = 0.0
            elif rps < 3.229:   # 0.2 - 8.2 mph
                mph = -0.1095 * rps**2 + 2.9318 * rps - 0.1412
            elif rps < 54.362:  # 8.2 - 136.0 mph
                mph = 0.0052 * rps**2 + 2.1980 * rps + 1.1091
            else:               # 136.0 - 181.5 mph
                mph = 0.1104 * rps**2 + 9.5685 * rps + 329.87
            debug("debugWind", "mph:", mph, "rps:", rps)
            return int(mph)
        elif addr == "dir":
            try:
                deg = (360 * dirTime / speedTime) % 360
            except ZeroDivisionError:
                deg = 0.0
        else:
            deg = 0.0
        debug("debugWind", "deg:", deg)
        return int(deg)

