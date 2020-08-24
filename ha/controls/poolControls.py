spaNotifyMsg = "Spa is ready"

import time
from ha import *
from ha.notification.notificationClient import *

# pump speed
pumpLo = 1
pumpMed = 2
pumpHi = 3
pumpMax = 4

# spa states
spaOff = 0
spaOn = 1           # pump max, heater enabled, light on
spaStarting = 2     # valves moving, pump starting, heater starting
spaWarming = 3      # pump reduced speed, heater on
spaStandby = 4      # pump reduced speed, heater enabled, light off
spaStopping = 5     # pump reduced speed, heater off

# valve positions
valvePool = 0
valveSpa = 1
valveOff = 2
valveMoving = 4

lxgControlPeriod = .1
poolValveTravelTime = 34

class SpaControl(Control):
    def __init__(self, name, interface, valveControl, pumpControl, heaterControl, lightApp, tempSensor, tempTargetControl,
            type="control", **kwargs):
        Control.__init__(self, name, interface, type=type, **kwargs)
        self.className = "Control"
        self.currentState = spaOff
        self.valveControl = valveControl
        self.pumpControl = pumpControl
        self.heaterControl = heaterControl
        self.lightApp = lightApp
        self.tempSensor = tempSensor
        self.tempTargetControl = tempTargetControl
        self.eventThread = None

        # state transition sequences
        self.startupSequence = Sequence("spaStartup",
                             [Cycle(self.valveControl, duration=0, startState=valveSpa),
                              Cycle(self.pumpControl, duration=0, startState=pumpMed, delay=30),
                              Cycle(self.heaterControl, duration=0, startState=on, delay=10)
                              ])
        self.onSequence = Sequence("spaOn",
                             [Cycle(self.pumpControl, duration=0, startState=pumpMax),
                              Cycle(self.lightApp, duration=0, startState=on),
                              ])
        self.standbySequence = Sequence("spaStandby",
                             [Cycle(self.pumpControl, duration=0, startState=pumpMed),
                              Cycle(self.lightApp, duration=0, startState=off),
                              ])
        self.shutdownSequence = Sequence("spaShutdown",
                             [Cycle(self.pumpControl, duration=0, startState=pumpMed),
                              Cycle(self.heaterControl, duration=0, startState=off),
                              Cycle(self.pumpControl, duration=0, startState=off, delay=60),
                              Cycle(self.valveControl, duration=0, startState=valvePool),
                              Cycle(self.lightApp, duration=0, startState=off, delay=30)
                              ])

    def getState(self, missing=None):
        debug('debugState', self.name, "getState ", self.currentState)
        return self.currentState

    # Implements the state diagram
    def setState(self, state):
        debug('debugState', self.name, "setState ", state, self.currentState)
        if state == spaOff:
            if (self.currentState == spaOn) or (self.currentState == spaStandby) or (self.currentState == spaWarming):
                self.stateTransition(spaStopping)
            elif (self.currentState == spaStarting) or (self.currentState == spaStopping) or (self.currentState == spaOff):
                debug('debugState', self.name, "setState ", "pass", state, self.currentState)
            else:
                debug('debugState', self.name, "unknown state", state, self.currentState)
        elif state == spaOn:
            if self.currentState == spaOff:
                self.stateTransition(spaStarting, spaOn)
            elif (self.currentState == spaStandby):
                self.stateTransition(spaOn)
            elif (self.currentState == spaStarting) or (self.currentState == spaStopping) or (self.currentState == spaOn) or (self.currentState == spaWarming):
                debug('debugState', self.name, "setState ", "pass", state, self.currentState)
            else:
                debug('debugState', self.name, "unknown state", state, self.currentState)
        elif state == spaStandby:
            if self.currentState == spaOff:
                self.stateTransition(spaStarting, spaStandby)
            elif (self.currentState == spaOn):
                self.stateTransition(spaStandby)
            elif (self.currentState == spaStarting) or (self.currentState == spaStopping) or (self.currentState == spaStandby) or (self.currentState == spaWarming):
                debug('debugState', self.name, "setState ", "pass", state, self.currentState)
            else:
                debug('debugState', self.name, "unknown state", state, self.currentState)
        else:
            log(self.name, "unknown state", state, self.currentState)

    # Implements state transitions
    def stateTransition(self, state, endState=None):
        debug('debugState', self.name, "stateTransition ", state, endState)
        if state == spaOn:
            self.onSequence.setState(sequenceStart, wait=True)
        elif state == spaStandby:
            self.standbySequence.setState(sequenceStart, wait=True)
        elif state == spaStarting:
            self.startupSequence.setState(sequenceStart, wait=False)
            self.startEventThread("spaStarting", self.startupSequence.getState, sequenceStopped, self.spaStarted, endState)
        elif state == spaStopping:
            self.shutdownSequence.setState(sequenceStart, wait=False)
            self.startEventThread("spaStopping", self.shutdownSequence.getState, sequenceStopped, self.stateTransition, spaOff)
        self.currentState = state

    # called when startup sequence is complete
    def spaStarted(self, endState):
        debug('debugState', self.name, "spaStarted ", endState)
        self.stateTransition(spaWarming)
        self.startEventThread("spaWarming", self.heaterControl.unitControl.getState, Off, self.spaReady, endState, self.heaterControl.unitControl.getState, On)

    # called when target temperature is reached
    def spaReady(self, state):
        debug('debugState', self.name, "spaReady ", state)
        self.stateTransition(state)
        notify("alertSpa", spaNotifyMsg+" "+str(int(self.tempSensor.getState()+.5))+" F")

    # start an event thread
    def startEventThread(self, name, checkFunction, checkValue, actionFunction, actionValue, waitFunction=None, waitValue=0):
        if self.eventThread:
            self.eventThread.cancel()
            self.eventThread = None
        self.eventThread = SpaEventThread(name, checkFunction, checkValue, actionFunction, actionValue, waitFunction, waitValue)
        self.eventThread.start()

# A thread to wait for the state of the specified sensor to reach the specified value
# then call the specified action function with the specified action value.
# Optionally, first wait for the state of a third function to reach a specified value.
class SpaEventThread(threading.Thread):
    def __init__(self, name, checkFunction, checkValue, actionFunction, actionValue, waitFunction=None, waitValue=0):
        threading.Thread.__init__(self, target=self.asyncEvent)
        self.name = name
        self.checkFunction = checkFunction
        self.checkValue = checkValue
        self.actionFunction = actionFunction
        self.actionValue = actionValue
        self.waitFunction = waitFunction
        self.waitValue = waitValue
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def asyncEvent(self):
        if self.waitFunction:
            debug('debugThread', self.name, "waiting")
            while self.waitFunction() != self.waitValue:
                time.sleep(1)
                if self.cancelled:
                    debug('debugThread', self.name, "cancelled")
                    return
        debug('debugThread', self.name, "started")
        while self.checkFunction() != self.checkValue:
            time.sleep(1)
            if self.cancelled:
                debug('debugThread', self.name, "cancelled")
                return
        self.actionFunction(self.actionValue)
        debug('debugThread', self.name, "finished")

# ColorSplash LXG pool light control

lxgColors = {"Peruvian paradise": 1,
	         "Supernova": 2,
		     "Northern lights": 3,
		     "Tidal wave": 4,
		     "Patriot dream": 5,
		     "Desert skies": 6,
		     "Nova": 7,
		     "Blue": 8,
		     "Green": 9,
		     "Red": 10,
		     "White": 11,
		     "Pink": 12,
		     "Save": 13,
		     "Orange": 14,
		     }

class LxgControl(MultiControl):
    def __init__(self, name, interface, lightControl, **kwargs):
        MultiControl.__init__(self, name, interface=interface, values=list(lxgColors.keys()),
                 **kwargs)
        self.type = "control"
        self.lightControl = lightControl

    def getState(self, missing=None):
        return ""

    def setState(self, state):
        debug('debugLxg', self.name, "setState", state)
        if self.lightControl.getState():    # light control must be on
            try:
                for i in range(lxgColors[state]):
                    time.sleep(lxgControlPeriod)
                    self.lightControl.setState(0)
                    time.sleep(lxgControlPeriod)
                    self.lightControl.setState(1)
            except KeyError:
                log(self.name, "unknown command", state)

class ValveControl(Control):
    def __init__(self, name, interface, valveControl, powerControl=None,
                    type="control", **kwargs):
        Control.__init__(self, name, interface=interface,
                    type=type, **kwargs)
        self.className = "Control"
        self.valveControl = valveControl
        self.powerControl = powerControl
        self.currentState = valvePool
        self.timer = None
        self.lock = threading.Lock()

    def getState(self, missing=None):
        return self.currentState

    def setState(self, value):
        debug('debugValves', self.name, "set", value)
        travelTime = poolValveTravelTime
        if value == self.currentState:
            return                              # nothing to do
        elif value == valveOff:
            if self.currentState != valveMoving:
                value = 1 - self.currentState           # move the opposite direction
                travelTime = poolValveTravelTime / 2    # off position is halfway
            else:
                return                          # ignore this case
        self.currentState = valveMoving
        self.notify()
        # cancel the timer if it is running
        if self.timer:
            self.timer.cancel()
        with self.lock:
            # start the motion
            debug('debugValves', self.name, "motion", value)
            self.valveControl.setState(value)
            # enable power
            if self.powerControl:
                debug('debugValves', self.name, "power on")
                self.powerControl.setState(1)
        # clean up and set the final state when motion is finished
        def doneMoving():
            with self.lock:
                # disable power
                if self.powerControl:
                    debug('debugValves', self.name, "power off")
                    self.powerControl.setState(0)
                self.currentState = value # done moving
                self.notify()
                debug('debugValves', self.name, "done", value)
        debug('debugValves', self.name, "starting", travelTime)
        self.timer = threading.Timer(travelTime, doneMoving)
        self.timer.start()
