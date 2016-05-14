unitOff = 0
unitOn = 1
unitEnabled = 4

unitTypeHeater = 0
unitTypeAc = 1

from ha.HAClasses import *

# a temperature controlled heating or cooling unit
class TempControl(HAControl):
    def __init__(self, name, interface, unitControl, tempSensor, tempTargetControl=None, unitType=0, hysteresis=1, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "HAControl"
        self.unitControl = unitControl      # the unit
        self.tempSensor = tempSensor          # the temp sensor
        self.tempTarget = 0
        self.tempTargetControl = tempTargetControl
        self.unitType = unitType
        self.hysteresis = hysteresis
        self.currentState = unitOff

    def getState(self, wait=False):
        debug('debugState', self.name, "getState ", self.currentState)
        return self.currentState

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        # thread to monitor the temperature
        def tempWatch():
            debug('debugTempControl', self.name, "tempWatch started")
            while self.currentState != unitOff:  # stop when state is set to off
                time.sleep(1)
                currentTemp = self.tempSensor.getState()
                if currentTemp > 0:                 # don't do anything if no temp reading
                    if self.tempTargetControl:
                        self.tempTarget = self.tempTargetControl.getState()
                    if self.currentState == unitOff:
                        debug('debugTempControl', self.name, "unit off")
                        self.unitControl.setState(unitOff)
                    elif self.currentState == unitOn:
                        if ((self.unitType == 0) and (currentTemp >= self.tempTarget + self.hysteresis)) or \
                           ((self.unitType == 1) and (currentTemp <= self.tempTarget - self.hysteresis)):
                            if self.unitControl.getState() != unitOff:
                                self.unitControl.setState(unitOff)
                                self.currentState = unitEnabled
                                debug('debugTempControl', self.name, "unit enabled")
                        else:
                            if self.unitControl.getState() != unitOn:
                                self.unitControl.setState(unitOn)
                                self.currentState = unitOn
                                debug('debugTempControl', self.name, "unit on")
                    elif self.currentState == unitEnabled:
                        if ((self.unitType == 0) and (currentTemp <= self.tempTarget - self.hysteresis)) or \
                           ((self.unitType == 1) and (currentTemp >= self.tempTarget + self.hysteresis)):
                            self.unitControl.setState(unitOn)
                            self.currentState = unitOn
                            debug('debugTempControl', self.name, "unit on")
                    else:
                        debug('debugTempControl', self.name, "unknown state", self.currentState)                    
            debug('debugTempControl', self.name, "tempWatch terminated")
        if state != unitOn:           # only allow explicit set on or off
            state = unitOff
        else:
            if self.currentState == unitOn:   # ignore multiple sets to on
                return
        self.currentState = state
        if self.currentState == unitOn:      # start the monitor thread when state set to on
            tempWatchThread = threading.Thread(target=tempWatch)
            tempWatchThread.start()
        self.notify()

    def setTarget(self, tempTarget, hysteresis=1, wait=False):
        debug('debugTempControl', self.name, "setTarget ", tempTarget, hysteresis)
        self.tempTarget = tempTarget
        self.hysteresis = hysteresis


