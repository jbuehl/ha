

import time
import threading
from ha import *

class VoltageSensor(Sensor):
    def __init__(self, name, interface, addr=None, threshold=0.0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.threshold = threshold
        self.lastVoltage = 0.0

    def getState(self):
        voltage = self.interface.read(self.addr) / 1000
        if abs(voltage - self.lastVoltage) > self.threshold:
            self.notify()
            self.lastVoltage = voltage
        return voltage

    def getLastState(self):
        return self.lastVoltage

class CurrentSensor(Sensor):
    def __init__(self, name, interface, addr, currentFactor, threshold=0.0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.currentFactor = currentFactor
        self.threshold = threshold
        self.lastCurrent = 0.0

    def getState(self):
        current = self.interface.read(self.addr) * self.currentFactor / 1000
        if current > self.threshold:
            if abs(current - self.lastCurrent) > self.threshold:
                # self.notify()
                self.lastCurrent = current
            return current
        else:
            return 0.0

    def getLastState(self):
        return self.lastCurrent

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
        power = self.currentSensor.getLastState() * self.voltage
        if power > self.threshold:
            if abs(power - self.lastPower) > self.threshold:
                # self.notify()
                self.lastPower = power
            return power
        else:
            return 0.0

    def getLastState(self):
        return self.lastPower

class EnergySensor(Sensor):
    def __init__(self, name, interface=None, addr=None, powerSensor=None, interval=10, resources=None,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.powerSensor = powerSensor
        self.interval = interval
        self.resources = resources
        self.energy = 0.0
        monitorEnergy = threading.Thread(target=self.monitorEnergy)
        monitorEnergy.daemon = True
        monitorEnergy.start()

    def getState(self):
        return self.energy

    def setState(self, value):
        self.energy = value

    def monitorEnergy(self):
        value = 0.0
        while True:
            if isinstance(self.powerSensor, str):
                if self.resources:
                    try:
                        value = self.resources[self.powerSensor].getLastState()
                    except KeyError:
                        value = 0.0
            else:
                value = self.powerSensor.getLastState()
            self.energy += value * self.interval / 3600
            time.sleep(self.interval)
