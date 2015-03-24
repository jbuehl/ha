
import time
import threading
from ha.GPIOInterface import *
from ha.HAClasses import *

# shade states
shadeUp = 0
shadeDown = 1
shadeRaising = 2
shadeLowering = 3

class ShadeInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.states = {0:0, 1:0, 2:0, 3:0}
        self.travelTime = [15, 15, 12, 12]
        self.timers = [None, None, None, None]
        self.gpio_lock = threading.Lock()

    def read(self, addr):
        try:
            return self.states[addr]
        except:
            return 0

    def write(self, addr, value):
        self.newValue = value
        self.states[addr] = value + 2  # moving
        self.sensorAddrs[addr].notify()

        if debugShades: log(self.name, "state", addr, self.states[addr])
        with self.gpio_lock:
            # set the direction
            if debugShades: log(self.name, "direction", addr*2, value)
            self.interface.write(addr*2, value)
            # start the motion
            if debugShades: log(self.name, "motion", addr*2+1, 1)
            self.interface.write(addr*2+1, 1)

        if self.timers[addr]:
            self.timers[addr].cancel()

        def _stop():
            with self.gpio_lock:
                # stop the motion
                if debugShades: log(self.name, "motion", addr*2+1, 1)
                self.interface.write(addr*2+1, 0)
                # reset the direction
                if debugShades: log(self.name, "direction", addr*2, 0)
                self.interface.write(addr*2, 0)
                self.states[addr] = self.newValue # done moving
                if debugShades: log(self.name, "state", addr, self.states[addr])
                self.sensorAddrs[addr].notify()

        self.timers[addr] = threading.Timer(self.travelTime[addr], _stop)
        self.timers[addr].start()

