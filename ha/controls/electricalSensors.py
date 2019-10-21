

import time
import threading
from ha import *

# Measure a voltage
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

# Measure a current
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
                self.notify()
            self.lastCurrent = current
            return current
        else:
            self.lastCurrent = current
            return 0.0

    def getLastState(self):
        return self.lastCurrent

# Compute power using a current measurement and a known voltage
class PowerSensor(Sensor):
    def __init__(self, name, interface=None, addr=None, currentSensor=None, voltage=0.0, threshold=0.0, pf=1.0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.currentSensor = currentSensor
        self.voltage = voltage
        self.threshold = threshold
        self.pf = pf
        self.lastPower = 0.0

    def getState(self):
        power = self.currentSensor.getLastState() * self.voltage * self.pf
        if power > self.threshold:
            if abs(power - self.lastPower) > self.threshold:
                self.notify()
            self.lastPower = power
            return power
        else:
            self.lastPower = power
            return 0.0

    def getLastState(self):
        return self.lastPower

# Accumulate the energy of a power measurement over time
class EnergySensor(Sensor):
    def __init__(self, name, interface=None, addr=None, powerSensor=None, interval=10, resources=None, persistence=None,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.powerSensor = powerSensor
        self.interval = interval
        self.resources = resources
        self.persistence = persistence  # FileInterface for state persistence
        if self.persistence:
            self.stateControl = Control(self.name+"State", self.persistence, self.name)
            self.energy = self.stateControl.getState()
            if self.energy == None:
                self.energy = 0.0
        else:
            self.energy = 0.0
        monitorEnergy = threading.Thread(target=self.monitorEnergy)
        monitorEnergy.start()

    def getState(self):
        return self.energy

    def setState(self, value):
        self.energy = value
        if self.persistence:
            self.stateControl.setState(value)

    # Thread to periodically compute energy over the specified interval
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
            if self.persistence:
                self.stateControl.setState(self.energy)
            time.sleep(self.interval)
