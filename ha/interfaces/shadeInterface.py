
import time
import threading
from ha.interfaces.gpioInterface import *
from ha import *

# shade states
shadeUp = 0
shadeDown = 1
shadeRaising = 2
shadeLowering = 3

class ShadeInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.states = {0:0, 1:0, 2:0, 3:0}
        self.travelTime = [15, 15, 12, 12]
        self.timers = [None, None, None, None]
        self.lock = threading.Lock()

    def read(self, addr):
        try:
            return self.states[addr]
        except:
            return 0

    def write(self, addr, value):
        self.newValue = value
        self.states[addr] = value + 2  # moving
        self.sensorAddrs[addr].notify()
        debug('debugShades', self.name, "state", addr, self.states[addr])
        # cancel the timer if it is running
        if self.timers[addr]:
            self.timers[addr].cancel()
        with self.lock:
            # set the direction
            debug('debugShades', self.name, "direction", addr, value)
            self.interface.write(addr*2, value)
            # start the motion
            debug('debugShades', self.name, "motion", addr, 1)
            self.interface.write(addr*2+1, 1)
        # clean up and set the final state when motion is finished
        def doneMoving():
            with self.lock:
                # stop the motion
                debug('debugShades', self.name, "motion", addr, 0)
                self.interface.write(addr*2+1, 0)
                # reset the direction
                debug('debugShades', self.name, "direction", addr, 0)
                self.interface.write(addr*2, 0)
                self.states[addr] = self.newValue # done moving
#                time.sleep(addr)    # wait a different amount of time for each shade - FIXME
                self.sensorAddrs[addr].notify()
                debug('debugShades', self.name, "state", addr, self.states[addr])
        self.timers[addr] = threading.Timer(self.travelTime[addr], doneMoving)
        self.timers[addr].start()

