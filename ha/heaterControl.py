heaterOff = 0
heaterOn = 1
heaterEnabled = 4

from ha.HAClasses import *

# a temperature controlled heater
class HeaterControl(HAControl):
    def __init__(self, name, interface, heaterControl, tempSensor, tempTargetControl=None, hysteresis=1, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "HAControl"
        self.heaterControl = heaterControl      # the heater
        self.tempSensor = tempSensor          # the temp sensor
        self.tempTarget = 0
        self.tempTargetControl = tempTargetControl
        self.hysteresis = hysteresis
        self.currentState = heaterOff

    def getState(self, wait=False):
        debug('debugState', self.name, "getState ", self.currentState)
        return self.currentState

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        # thread to monitor the temperature
        def tempWatch():
            debug('debugHeater', self.name, "tempWatch started")
            while self.currentState != heaterOff:  # stop when state is set to off
                time.sleep(1)
                currentTemp = self.tempSensor.getState()
                if currentTemp > 0:                 # don't do anything if no temp reading
                    if self.tempTargetControl:
                        self.tempTarget = self.tempTargetControl.getState()
                    if self.currentState == heaterOff:
                        debug('debugHeater', self.name, "heater off")
                        self.heaterControl.setState(heaterOff)
                    elif self.currentState == heaterOn:
                        if currentTemp >= self.tempTarget + self.hysteresis:
                            if self.heaterControl.getState() != heaterOff:
                                self.heaterControl.setState(heaterOff)
                                self.currentState = heaterEnabled
                                debug('debugHeater', self.name, "heater enabled")
                        else:
                            if self.heaterControl.getState() != heaterOn:
                                self.heaterControl.setState(heaterOn)
                                self.currentState = heaterOn
                                debug('debugHeater', self.name, "heater on")
                    elif self.currentState == heaterEnabled:
                        if currentTemp <= self.tempTarget - self.hysteresis:
                            self.heaterControl.setState(heaterOn)
                            self.currentState = heaterOn
                            debug('debugHeater', self.name, "heater on")
                    else:
                        debug('debugHeater', self.name, "unknown state", self.currentState)                    
            debug('debugHeater', self.name, "tempWatch terminated")
        if state != heaterOn:           # only allow explicit set on or off
            state = heaterOff
        else:
            if self.currentState == heaterOn:   # ignore multiple sets to on
                return
        self.currentState = state
        if self.currentState == heaterOn:      # start the monitor thread when state set to on
            tempWatchThread = threading.Thread(target=tempWatch)
            tempWatchThread.start()
        self.notify()

    def setTarget(self, tempTarget, hysteresis=1, wait=False):
        debug('debugHeater', self.name, "setTarget ", tempTarget, hysteresis)
        self.tempTarget = tempTarget
        self.hysteresis = hysteresis


