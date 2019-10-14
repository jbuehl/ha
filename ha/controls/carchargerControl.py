
# https://en.wikipedia.org/wiki/SAE_J1772
# http://abyz.me.uk/rpi/pigpio/python.html
# https://openev.freshdesk.com/support/home
# https://www.barbouri.com/2016/06/16/the-diy-open-evse-project/

import pigpio
import time
import threading
from ha import *
#from ha.notification import *

# GPIO pins
pilotPin = 18
relayPin = 23
readyLed = 24
faultLed = 25

# J1772 states
off = 0
on = 1
ready = 1
connected = 2
charging = 3
fault = 4

# Voltage thresholds
maxVolts = 12/3         # 4V
unpluggedVolts = 10.5/3 # 3.5V
connectedVolts = 7.5/3  # 2.5V
chargingVolts = 4.5/3   # 1.5V

# current sensor parameters
currentFactor = 10  # = 50A / 5V
powerThreshold = 10.0
voltageThreshold = 0.1

# general parameters
chargingVoltage = 240       # volts
maxCurrent = 30             # amps
sampleInterval = 1          # seconds
pilotFreq = 1000            # Hz

class VoltageSensor(Sensor):
    def __init__(self, name, interface, addr=None,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.lastVoltage = 0.0

    def getState(self):
        voltage = self.interface.read(self.addr) / 1000
        if abs(voltage - self.lastVoltage) > voltageThreshold:
            self.notify()
            self.lastVoltage = voltage
        return voltage

class PowerSensor(Sensor):
    def __init__(self, name, interface, addr=None,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.lastPower = 0.0

    def getState(self):
        adcVolts = self.interface.read(self.addr)
        power = chargingVoltage * currentFactor * adcVolts / 1000
        if power > powerThreshold:
            if abs(power - self.lastPower) > powerThreshold:
                self.notify()
                self.lastPower = power
            return power
        else:
            return 0.0

class CarChargerControl(Control):
    def __init__(self, name, interface, voltageSensor, currentSensor, addr=None,
            group="", type="control", location=None, label="", interrupt=None, event=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Control"
        self.eventThread = None
        self.voltageSensor = voltageSensor
        self.currentSensor = currentSensor
        self.pilotVolts = 0.0
        self.chargeCurrent = 0.0
        self.gpio = pigpio.pi()
        self.stop()

    def gpioWrite(self, pin, value):
        self.gpio.write(pin, value)

    def start(self):
        debug('debugCarcharger', self.name, "starting")
        self.pilotState = on
        self.gpioWrite(pilotPin, on)
        self.gpioWrite(relayPin, off)
        self.gpioWrite(readyLed, on)
        self.gpioWrite(faultLed, off)
        chargerThread = threading.Thread(target=self.charger)
        chargerThread.start()

    def charger(self):
        # control loop
        self.running = True
        while self.running:
            # sample pilot voltage
            self.pilotVolts = self.voltageSensor.getState()
            self.chargeCurrent = self.currentSensor.getState()
            # J1772 state machine
            if (self.pilotVolts < maxVolts) and (self.pilotVolts > unpluggedVolts):
                # unplugged
                if self.pilotState != ready:
                    self.pilotState = ready
                    self.gpioWrite(pilotPin, on)
                    self.gpioWrite(relayPin, off)
                    self.notify()
                    debug('debugCarcharger', self.name, "ready", self.pilotVolts, self.chargeCurrent)
            elif self.pilotVolts > connectedVolts:
                # connected
                if self.pilotState != connected:
                    self.pilotState = connected
                    dutyCycle = int(maxCurrent/.6)   # percent
                    self.gpio.hardware_PWM(pilotPin, pilotFreq, dutyCycle*10000)
                    self.gpioWrite(relayPin, off)
                    self.notify()
                    debug('debugCarcharger', self.name, "connected", self.pilotVolts, self.chargeCurrent)
            elif self.pilotVolts > chargingVolts:
                # charging
                if self.pilotState == connected:
                    self.pilotState = charging
                    self.gpioWrite(relayPin, on)
                    self.notify()
                    debug('debugCarcharger', self.name, "charging", self.pilotVolts, self.chargeCurrent)
            else:
                # error
                self.pilotState = fault
                self.gpioWrite(pilotPin, off)
                self.gpioWrite(relayPin, off)
                self.gpioWrite(readyLed, off)
                self.gpioWrite(faultLed, on)
                self.running = False
                self.notify()
                debug('debugCarcharger', self.name, "fault", self.pilotVolts, self.chargeCurrent)
            time.sleep(sampleInterval)

    def stop(self):
        debug('debugCarcharger', self.name, "stopping")
        self.running = False
        time.sleep(sampleInterval)
        self.pilotState = off
        self.gpioWrite(pilotPin, off)
        self.gpioWrite(relayPin, off)
        self.gpioWrite(readyLed, off)
        self.gpioWrite(faultLed, off)
        self.notify()

    def getState(self):
        return self.pilotState

    def setState(self, value):
        if value:
            self.start()
        else:
            self.stop()
