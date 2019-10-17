
import time
from ha import *

class VoltageSensor(Sensor):
    def __init__(self, name, interface, addr=None, threshold=0.0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.threshold = threshold
        self.lastVoltage = 0.0

    def getState(self):
        time.sleep(.01)  # limit read rate
        voltage = self.interface.read(self.addr) / 1000
        if abs(voltage - self.lastVoltage) > self.threshold:
            self.notify()
            self.lastVoltage = voltage
        return voltage

class CurrentSensor(Sensor):
    def __init__(self, name, interface, addr, currentFactor, threshold=0.0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.currentFactor = currentFactor
        self.threshold = threshold
        self.lastCurrent = 0.0

    def getState(self):
        time.sleep(.01)  # limit read rate
        current = self.interface.read(self.addr) * self.currentFactor / 1000
        if current > self.threshold:
            if abs(current - self.lastCurrent) > self.threshold:
                # self.notify()
                self.lastCurrent = current
            return current
        else:
            return 0.0

class PowerSensor(Sensor):
    def __init__(self, name, interface=None, addr=None, currentSensor=None, voltage=0.0, threshold=0.0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.currentSensor = currentSensor
        self.voltage = voltage
        self.threshold = threshold
        self.lastPower = 0.0

    def getState(self):
        power = self.currentSensor.getState() * self.voltage
        if power > self.threshold:
            if abs(power - self.lastPower) > self.threshold:
                # self.notify()
                self.lastPower = power
            return power
        else:
            return 0.0
