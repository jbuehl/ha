# Calculate wind speed and direction using the Peet Ultimeter Pro Anemometer
timeOut = 10

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
    if state == 0:
        speedTime = curTime - startTime
        startTime = curTime

# wind vane contact closure interrupt routine
def dirInterrupt(sensor, state):
    global startTime, speedTime, dirTime
    curTime = time.time()
    if state == 0:
        dirTime = curTime - startTime

class WindInterface(Interface):
    def __init__(self, name, interface, anemometer, windVane, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.anemometer = anemometer    # anemometer contact closure sensor
        self.anemometer.interrupt = speedInterrupt
        self.windVane = windVane        # wind vane contact closure sensor
        self.windVane.interrupt = dirInterrupt
        self.speed = 0.0
        self.dir = 0.0
        debug("debugWind", self.name, "anemometer:", self.anemometer.name, "windVane:", self.windVane.name)

    def read(self, addr):
        curTime = time.time() - startTime
        debug("debugWind", self.name, "read", "addr:", addr, "startTime:", startTime, "curTime:", curTime)
        if addr == "speed":
            # if no data for timeOut seconds, there is no wind
            if curTime > timeOut:
                rps = 0
                self.speed = 0.0
            else:
                # calculate revolutions per second
                try:
                    rps = 1.0 / speedTime
                except ZeroDivisionError:
                    rps = 0.0
                # calculate the wind speed
                if rps < .010:
                    self.speed = 0.0
                elif rps < 3.229:   # 0.2 - 8.2 speed
                    self.speed = -0.1095 * rps**2 + 2.9318 * rps - 0.1412
                elif rps < 54.362:  # 8.2 - 136.0 speed
                    self.speed = 0.0052 * rps**2 + 2.1980 * rps + 1.1091
                else:               # 136.0 - 181.5 speed
                    # self.speed = 0.1104 * rps**2 + 9.5685 * rps + 329.87
                    self.speed = 0.0    # throw out values > 136 mph
            debug("debugWind", self.name, "speedTime:", speedTime, "rps:", rps, "speed:", self.speed)
            return int(self.speed + .5)
        elif addr == "dir":
            # calculate direction only if there is wind
            if self.speed > 0.0:
                try:
                    self.dir = (180 + (360 * dirTime / speedTime)) % 360
                except ZeroDivisionError:
                    self.dir = 0.0
                debug("debugWind", self.name, "dirTime:", dirTime, "speedTime:", speedTime, "direction:", self.dir)
            return int(self.dir + .5)
        else:
            return 0.0
