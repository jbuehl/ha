poolValveTravelTime = 35

import time
import threading
from ha.interfaces.gpioInterface import *
from ha import *

# valve states
valveMoving = 4

class ValveInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.travelTime = poolValveTravelTime
        self.timers = {}
        self.lock = threading.Lock()

    def read(self, addr):
        try:
            return self.states[addr]
        except:
            return 0

    def write(self, addr, value):
#        self.newValue = value
        debug('debugValves', self.name, "start", addr, self.states[addr])
        self.states[addr] = valveMoving
        self.sensorAddrs[addr].notify()
        # cancel the timer if it is running
        if self.timers[addr]:
            self.timers[addr].cancel()
        with self.lock:
            # start the motion
            debug('debugValves', self.name, "motion", addr, self.states[addr])
            self.interface.write(addr, value)
        # clean up and set the final state when motion is finished
        def doneMoving():
            with self.lock:
                self.states[addr] = value # done moving
                self.sensorAddrs[addr].notify()
                debug('debugValves', self.name, "done", addr, self.states[addr])
        self.timers[addr] = threading.Timer(self.travelTime, doneMoving)
        self.timers[addr].start()

    def addSensor(self, sensor):
        Interface.addSensor(self, sensor)
        self.timers[sensor.addr] = None
        self.states[sensor.addr] = 0    # initialize state to 0
