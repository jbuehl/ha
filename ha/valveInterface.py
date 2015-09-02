poolValveTravelTime = 35

import time
import threading
from ha.GPIOInterface import *
from ha.HAClasses import *

# valve states
valveMoving = 2

class ValveInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.travelTime = poolValveTravelTime
        self.timers = {}
        self.lock = threading.Lock()

    def read(self, addr):
        try:
            return self.states[addr]
        except:
            return 0

    def write(self, addr, value):
        self.newValue = value
        self.states[addr] = valveMoving
        self.sensorAddrs[addr].notify()
        debug('debugValves', self.name, "state", addr, self.states[addr])
        # cancel the timer if it is running
        if self.timers[addr]:
            self.timers[addr].cancel()
        with self.lock:
            # start the motion
            debug('debugValves', self.name, "motion", addr, value)
            self.interface.write(addr, value)
        # clean up and set the final state when motion is finished
        def doneMoving():
            with self.lock:
                self.states[addr] = self.newValue # done moving
                self.sensorAddrs[addr].notify()
                debug('debugValves', self.name, "state", addr, self.states[addr])
        self.timers[addr] = threading.Timer(self.travelTime, doneMoving)
        self.timers[addr].start()

    def addSensor(self, sensor):
        self.timers[sensor.addr] = None
        HAInterface.addSensor(self, sensor)
