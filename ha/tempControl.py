inhibitDelay = 60
inhibitState = 1

# state values
controlOff = 0
controlOn = 1
controlEnabled = 4
unitOff = 0
unitOn = 1

unitTypeHeater = 0
unitTypeAc = 1

from ha.HAClasses import *

# a temperature controlled heating or cooling unit
class TempControl(HAControl):
    def __init__(self, name, interface, unitControl, tempSensor, tempTargetControl=None, inhibitSensor=None, unitType=0, hysteresis=1, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "HAControl"
        self.unitControl = unitControl              # the control for the heating or cooling unit
        self.tempSensor = tempSensor                # associated temp sensor
        self.tempTargetControl = tempTargetControl  # the control that sets the temp target
        self.tempTarget = 0                         # current temp target value
        self.inhibitSensor = inhibitSensor          # sensor that inhibits tempControl operation if it is on
        self.unitType = unitType                    # type of unit
        self.hysteresis = hysteresis
        self.controlState = controlOff
        # inhibit the tempControl after a delay
        def inhibitTimer():
            debug('debugTempControl', self.name, "inhibitTimer ended")
            self.inhibit = True
        # thread to monitor the state of the inhibit sensor
        def inhibitWatch():
            debug('debugTempControl', self.name, "inhibitWatch started")
            inhibitTimerThread = None
            while True:
                if self.inhibitSensor.event:        # wait for inhibitSensor state to change
                    self.inhibitSensor.event.wait()
                else:                               # poll inhibitSensor state
                    time.sleep(1)
                if self.inhibitSensor.getState() == inhibitState:
                    if not inhibitTimerThread:      # start the delay timer
                        inhibitTimerThread = threading.Timer(inhibitDelay, inhibitTimer)
                        inhibitTimerThread.start()
                        debug('debugTempControl', self.name, "inhibitTimer started")
                else:                               # state changed back, cancel the timer and enable the tempControl
                    self.inhibit = False
                    if inhibitTimerThread:
                        inhibitTimerThread.cancel()
                        debug('debugTempControl', self.name, "inhibitTimer cancelled")
                        inhibitTimerThread = None
        self.inhibit = False
        if self.inhibitSensor:                      # start the thread to watch the state of the inhibit sensor
            inhibitWatchThread = threading.Thread(target=inhibitWatch)
            inhibitWatchThread.start()

    def getState(self, wait=False):
        debug('debugState', self.name, "getState ", self.controlState)
        return self.controlState

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        # thread to monitor the temperature
        def tempWatch():
            debug('debugTempControl', self.name, "tempWatch started")
            while self.controlState != unitOff:  # stop when state is set to off
                time.sleep(1)
                currentTemp = self.tempSensor.getState()
                if currentTemp > 0:                 # don't do anything if no temp reading
                    if self.tempTargetControl:
                        self.tempTarget = self.tempTargetControl.getState()
                    if self.controlState == controlOff:
                        debug('debugTempControl', self.name, "unit off")
                        self.unitControl.setState(unitOff)
                    elif self.controlState == controlOn:
                        if self.inhibit or \
                            ((self.unitType == 0) and (currentTemp >= self.tempTarget + self.hysteresis)) or \
                            ((self.unitType == 1) and (currentTemp <= self.tempTarget - self.hysteresis)):
                            if self.unitControl.getState() != unitOff:
                                self.unitControl.setState(unitOff)
                                self.controlState = controlEnabled
                                debug('debugTempControl', self.name, "unit off")
                        else:
                            if self.unitControl.getState() != unitOn:
                                self.unitControl.setState(unitOn)
                                self.controlState = controlOn
                                debug('debugTempControl', self.name, "unit on")
                    elif self.controlState == controlEnabled:
                        if not self.inhibit:
                            if ((self.unitType == 0) and (currentTemp <= self.tempTarget - self.hysteresis)) or \
                                ((self.unitType == 1) and (currentTemp >= self.tempTarget + self.hysteresis)):
                                self.unitControl.setState(unitOn)
                                self.controlState = controlOn
                                debug('debugTempControl', self.name, "unit on")
                    else:
                        debug('debugTempControl', self.name, "unknown state", self.controlState)                    
            debug('debugTempControl', self.name, "tempWatch terminated")
        if state != controlOn:           # only allow explicit set on or off
            state = controlOff
        else:
            if self.controlState == controlOn:   # ignore multiple sets to on
                return
        self.controlState = state
        if self.controlState == controlOn:      # start the monitor thread when state set to on
            tempWatchThread = threading.Thread(target=tempWatch)
            tempWatchThread.start()
        self.notify()

    def setTarget(self, tempTarget, hysteresis=1, wait=False):
        debug('debugTempControl', self.name, "setTarget ", tempTarget, hysteresis)
        self.tempTarget = tempTarget
        self.hysteresis = hysteresis


