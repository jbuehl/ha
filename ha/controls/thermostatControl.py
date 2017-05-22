modeOff = 0
modeHeat = 1
modeCool = 2
modeFan = 3
modeAuto = 4

heatOff = 0
heatOn = 1
heatEnabled = 4

coolOff = 0
coolOn = 1
coolEnabled = 4

from ha import *

# thermostat control for heating and cooling
class ThermostatControl(Control):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface, heatControl, coolControl, fanControl, tempSensor, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "Control"
        self.heatControl = heatControl        # the heat
        self.coolControl = coolControl        # the A/C
        self.fanControl = fanControl          # the fan
        self.tempSensor = tempSensor          # the temp sensor
        self.tempTarget = 0
        self.currentState = modeOff
        self.heatState = heatOff
        self.coolState = coolOff

    def getState(self, wait=False):
        debug('debugState', self.name, "getState ", self.currentState)
        return self.currentState

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        # thread to monitor the temperature
        def tempWatch():
            debug('debugThermostat', self.name, "tempWatch started")
            while self.currentState != heatOff:  # stop when state is set to off
                time.sleep(1)
                if self.currentState == heatOff:
                    debug('debugThermostat', self.name, "heat off")
                    self.heatControl.setState(heatOff)
                elif self.currentState == heatOn:
                    if self.tempSensor.getState() >= self.tempTarget + self.hysteresis:
                        if self.heatControl.getState() != heatOff:
                            self.heatControl.setState(heatOff)
                            self.currentState = heatEnabled
                            debug('debugThermostat', self.name, "heat enabled")
                    else:
                        if self.heatControl.getState() != heatOn:
                            self.heatControl.setState(heatOn)
                            self.currentState = heatOn
                            debug('debugThermostat', self.name, "heat on")
                elif self.currentState == heatEnabled:
                    if self.tempSensor.getState() <= self.tempTarget - self.hysteresis:
                        self.heatControl.setState(heatOn)
                        self.currentState = heatOn
                        debug('debugThermostat', self.name, "heat on")
                else:
                    debug('debugThermostat', self.name, "unknown state", self.currentState)                    
            debug('debugThermostat', self.name, "tempWatch terminated")
        if state != heatOn:           # only allow explicit set on or off
            state = heatOff
        else:
            if self.currentState == heatOn:   # ignore multiple sets to on
                return
        self.currentState = state
        if self.currentState == heatOn:      # start the monitor thread when state set to on
            tempWatchThread = threading.Thread(target=tempWatch)
            tempWatchThread.start()
        self.notify()

    def setTarget(self, tempTarget, hysteresis=1, wait=False):
        debug('debugThermostat', self.name, "setTarget ", tempTarget, hysteresis)
        self.tempTarget = tempTarget
        self.hysteresis = hysteresis


