tempWatchInterval = 1

# states
enabled = 1

# unit types
unitTypeHeater = 0
unitTypeAc = 1

from ha import *

# a temperature controlled heating or cooling unit
class TempControl(Control):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface, unitControl, tempSensor, 
                tempTargetControl=None, unitType=0, hysteresis=1, 
                addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "Control"
        self.unitControl = unitControl              # the control for the heating or cooling unit
        self.tempSensor = tempSensor                # associated temp sensor
        self.tempTargetControl = tempTargetControl  # the control that sets the temp target
        self.tempTarget = 0                         # current temp target value
        self.unitType = unitType                    # type of unit: 0=heater, 1=cooler
        self.hysteresis = hysteresis                # how much to overshoot or undershoot the temp target
        self.controlState = off                     # state of this control
        self.inhibited = False                      # this control is inhibited
        
    def getState(self, wait=False):
        debug('debugState', self.name, "getState ", self.controlState)
        return self.controlState

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        # thread to monitor the temperature
        def tempWatch():
            debug('debugTempControl', self.name, "tempWatch started")
            while self.controlState == enabled:  # stop when state is set to off
                time.sleep(tempWatchInterval)
                currentTemp = self.tempSensor.getState()
                if currentTemp > 0:                 # don't do anything if no temp reading
                    if self.tempTargetControl:
                        self.tempTarget = self.tempTargetControl.getState()
                    debug('debugTempControlTemp', self.name, "currentTemp:", currentTemp, "targetTemp:", self.tempTarget, "inhibit:", self.inhibited)
                    if self.inhibited or \
                        ((self.unitType == unitTypeHeater) and (currentTemp >= self.tempTarget + self.hysteresis)) or \
                        ((self.unitType == unitTypeAc) and (currentTemp <= self.tempTarget - self.hysteresis)):
                        # unit is inhibited or the target temp has been reached
                        if self.unitControl.getState() != off:
                            # turn the unit off
                            self.unitControl.setState(off)
                            debug('debugTempControl', self.name, "unit off")
                    elif not self.inhibited and \
                        (((self.unitType == unitTypeHeater) and (currentTemp <= self.tempTarget - self.hysteresis)) or \
                        ((self.unitType == unitTypeAc) and (currentTemp >= self.tempTarget + self.hysteresis))):
                        # unit is not inhibited and the temp is sufficiently off target
                        if self.unitControl.getState() != on:
                            # turn the unit on
                            self.unitControl.setState(on)
                            debug('debugTempControl', self.name, "unit on")
                    else:
                        # do nothing
                        pass
            debug('debugTempControl', self.name, "tempWatch terminated")
        self.controlState = state
        if self.controlState == enabled:      # start the monitor thread when state set to enabled
            tempWatchThread = threading.Thread(target=tempWatch)
            tempWatchThread.start()
        self.notify()

    def setTarget(self, tempTarget, hysteresis=1, wait=False):
        debug('debugTempControl', self.name, "setTarget ", tempTarget, hysteresis)
        self.tempTarget = tempTarget
        self.hysteresis = hysteresis

    def setInhibit(self, value):
        debug('debugTempControl', self.name, "inhibit", value)
        self.inhibited = value
