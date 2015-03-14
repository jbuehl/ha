
import time
import threading
from ha.GPIOInterface import *
from ha.HAClasses import *

class ShadeInterface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)
        self.state = [0, 0, 0, 0]
        self.travelTime = [15, 15, 12, 12]
        self.timers = [None, None, None, None]
        self.gpio_lock = threading.Lock()

    def read(self, addr):
        try:
            return self.state[addr]
        except:
            return 0

    def write(self, addr, value):
        self.newValue = value
        self.state[addr] = value + 2  # moving

        if debugShades: log(self.name, "state", addr, self.state[addr])
        with self.gpio_lock:
            # set the direction
            if debugShades: log(self.name, "direction", addr*2, value)
            self.interface.write(GPIOAddr(0, 0, addr*2, 1), value)
            # start the motion
            if debugShades: log(self.name, "motion", addr*2+1, 1)
            self.interface.write(GPIOAddr(0, 0, addr*2+1, 1), 1)

        if self.timers[addr]:
            self.timers[addr].cancel()

        def _stop():
            with self.gpio_lock:
                # stop the motion
                if debugShades: log(self.name, "motion", addr*2+1, 1)
                self.interface.write(GPIOAddr(0, 0, addr*2+1, 1), 0)
                # reset the direction
                if debugShades: log(self.name, "direction", addr*2, 0)
                self.interface.write(GPIOAddr(0, 0, addr*2, 1), 0)
                self.state[addr] = self.newValue # done moving
                if debugShades: log(self.name, "state", addr, self.state[addr])

        self.timers[addr] = threading.Timer(self.travelTime[addr], _stop)
        self.timers[addr].start()

