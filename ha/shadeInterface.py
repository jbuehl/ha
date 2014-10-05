
import time
import threading
from ha.GPIOInterface import *
from ha.HAClasses import *

class ShadeInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)
        self.state = [0, 0, 0, 0]
        self.travelTime = [15, 15, 12, 12]
        self.timers = [None, None, None, None]
        self.gpio_lock = threading.Lock()

    def read(self, theAddr):
        try:
            return self.state[theAddr]
        except:
            return 0

    def write(self, theAddr, theValue):
        self.newValue = theValue
        self.state[theAddr] = theValue + 2  # moving

        with self.gpio_lock:
            # set the direction
            self.interface.write(GPIOAddr(0, 0, theAddr*2, 1), theValue)
            # start the motion
            self.interface.write(GPIOAddr(0, 0, theAddr*2+1, 1), 1)

        if self.timers[theAddr]:
            self.timers[theAddr].cancel()

        def _stop():
            with self.gpio_lock:
                # stop the motion
                self.interface.write(GPIOAddr(0, 0, theAddr*2+1, 1), 0)
                # reset the direction
                self.interface.write(GPIOAddr(0, 0, theAddr*2, 1), 0)
                self.state[theAddr] = self.newValue # done moving

        self.timers[theAddr] = threading.Timer(self.travelTime[theAddr], _stop)
        self.timers[theAddr].start()

