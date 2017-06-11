# state values
modeOff = 0
modeHeat = 1
modeCool = 2
modeFan = 3
modeAuto = 4

inhibitDelay = 60
inhibitState = 1
inhibitWatchInterval = 1

from ha import *

# thermostat control for heating and cooling
class ThermostatControl(Control):
    objectArgs = ["interface", "event"]
    def __init__(self, name, heatControl, coolControl, fanControl, inhibitSensor=None, persistenceControl=None,
                interface=None, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None, event=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt, event=event)
        self.className = "Control"
        self.heatControl = heatControl                  # the heating unit
        self.coolControl = coolControl                  # the A/C unit
        self.fanControl = fanControl                    # the fan unit
        self.inhibitSensor = inhibitSensor              # sensor that inhibits thermostat operation if it is on
        self.persistenceControl = persistenceControl    # persistent storage of the state
        self.inhibited = False

    def start(self):
        currentState = self.persistenceControl.getState()
        if currentState == None:
            self.setState(modeOff)
        else:
            self.setState(currentState)
        
        # inhibit the tempControl after a delay
        def inhibitTimer():
            debug('debugThermostat', self.name, "inhibitTimer ended")
            self.setInhibit(True)
            
        # thread to monitor the state of the inhibit sensor
        def inhibitWatch():
            debug('debugThermostat', self.name, "inhibitWatch started")
            inhibitTimerThread = None
            while True:
                if self.inhibitSensor.event:        # wait for inhibitSensor state to change
                    self.inhibitSensor.event.wait()
                else:                               # poll inhibitSensor state
                    time.sleep(inhibitWatchInterval)
                if self.inhibitSensor.getState() == inhibitState:
                    if not inhibitTimerThread:      # start the delay timer
                        inhibitTimerThread = threading.Timer(inhibitDelay, inhibitTimer)
                        inhibitTimerThread.start()
                        debug('debugThermostat', self.name, "inhibitTimer started")
                else:
                    if self.inhibited:                               # state changed back, cancel the timer and enable the thermostat
                        self.setInhibit(False)
                    if inhibitTimerThread:
                        inhibitTimerThread.cancel()
                        debug('debugThermostat', self.name, "inhibitTimer cancelled")
                        inhibitTimerThread = None

        self.inhibited = False
        if self.inhibitSensor:                      # start the thread to watch the state of the inhibit sensor
            inhibitWatchThread = threading.Thread(target=inhibitWatch)
            inhibitWatchThread.start()

    def setInhibit(self, value):
        debug('debugThermostat', self.name, "inhibit", value)
        self.inhibited = value
        self.heatControl.setInhibit(value)
        self.coolControl.setInhibit(value)
    
    def getState(self, wait=False):
        debug('debugState', self.name, "getState ", self.currentState)
        return self.currentState

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        if state == modeOff:
            self.heatControl.setState(off)
            self.coolControl.setState(off)
            self.fanControl.setState(off)
        elif state == modeHeat:
            self.heatControl.setState(on)
            self.coolControl.setState(off)
            self.fanControl.setState(off)
        elif state == modeCool:
            self.heatControl.setState(off)
            self.coolControl.setState(on)
            self.fanControl.setState(off)
        elif state == modeFan:
            self.heatControl.setState(off)
            self.coolControl.setState(off)
            self.fanControl.setState(on)
        elif state == modeAuto:
            self.heatControl.setState(on)
            self.coolControl.setState(on)
            self.fanControl.setState(off)
        else:
            debug('debugThermostat', self.name, "unknown state", state)
            return
        self.currentState = state
        if self.persistenceControl:
            self.persistenceControl.setState(state)                    
        self.notify()

heatOn = modeHeat
coolOn = modeCool
fanOn = modeFan
hold = 5

# Sensor that returns the thermostat unit control that is currently running
class ThermostatUnitSensor(Sensor):
    def __init__(self, name, thermostatControl, interface=None, addr=None, group="", type="sensor", location=None, label="", view=None, interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.thermostatControl = thermostatControl

    def getState(self):
        # assume only one of them is on
        if self.thermostatControl.getState() == Off:
            return Off
        elif self.thermostatControl.inhibited:
            return hold
        elif self.thermostatControl.heatControl.unitControl.getState() == On:
            return heatOn
        elif self.thermostatControl.coolControl.unitControl.getState() == On:
            return coolOn
        if self.thermostatControl.fanControl.getState() == On:
            return fanOn
        else:
            return Off
        
    

