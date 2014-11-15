
import time
import threading
from ha.HAClasses import *

# state values
off = 0
on = 1

pumpLo = 1
pumpMed = 2
pumpHi = 3
pumpMax = 4

spaOff = 0
spaOn = 1
spaStarting = 2
spaWarming = 3
spaStandby = 4
spaStopping = 5

seqStop = 0
seqStart = 1
seqStopped = 0
seqRunning = 1

valvesPool = 0
valvesSpa = 1

class SpaInterface(HAInterface):
    def __init__(self, name, valveControl, pumpControl, heaterControl, lightControl, tempSensor):
        HAInterface.__init__(self, name, None)
        self.state = spaOff
        self.valveControl = valveControl
        self.pumpControl = pumpControl
        self.heaterControl = heaterControl
        self.lightControl = lightControl
        self.tempSensor = tempSensor
        
        # state transition sequences
        self.startupSequence = HASequence("spaStartup", 
                             [HACycle(self.valveControl, duration=0, startState=valvesSpa),
                              HACycle(self.pumpControl, duration=0, startState=pumpMed, delay=30),
                              HACycle(self.heaterControl, duration=30, startState=on, delay=10)
                              ])
        self.onSequence = HASequence("spaOn", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMax),
                              HACycle(self.lightControl, duration=0, startState=on)
                              ])
        self.standbySequence = HASequence("spaStandby", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMed),
                              HACycle(self.lightControl, duration=0, startState=on)
                              ])
        self.shutdownSequence = HASequence("spaShutdown", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMed),
                              HACycle(self.heaterControl, duration=0, startState=off),
                              HACycle(self.pumpControl, duration=0, startState=off, delay=300),
                              HACycle(self.valveControl, duration=0, startState=valvesPool),
                              HACycle(self.lightControl, duration=0, startState=off, delay=30)
                              ])

    def read(self, addr):
        return self.state

    def write(self, addr, value):
    # Implements the state diagram
        if value == spaOff:
            if (self.state == spaOn) or (self.state == spaStandby) or (self.state == spaWarming):
                self.setState(spaStopping)
            elif (self.state == spaStarting) or (self.state == spaStopping) or (self.state == spaOff):
                pass
        elif value == spaOn:
            if self.state == spaOff:
                self.setState(spaStarting, spaOn)
            elif (self.state == spaStandby) or (self.state == spaWarming):
                self.setState(spaOn)
            elif (self.state == spaStarting) or (self.state == spaStopping) or (self.state == spaOn):
                pass
        elif value == spaStandby:
            if self.state == spaOff:
                self.setState(spaStarting, spaOn)
            elif (self.state == spaOn) or (self.state == spaWarming):
                self.setState(spaStandby)
            elif (self.state == spaStarting) or (self.state == spaStopping) or (self.state == spaStandby):
                pass
        else:
            log(self.name, "unknown state", value)

    def setState(self, state, endState=None):
    # Implements state transitions
        if debugState: log(self.name, "setState ", state)
        if state == spaOn:
            self.onSequence.setState(seqStart, wait=True)
        elif state == spaStandby:
            self.standbySequence.setState(seqStart, wait=True)
        elif state == spaStarting:
            self.startupSequence.setState(seqStart, wait=False)
            startEvent = EventThread("spaStarting", self.startupSequence.getState, seqStopped, self.setState, spaWarming)
            startEvent.start()
            tempEvent = EventThread("spaWarming", self.tempSensor.getState, spaTempTarget, self.setState, endState)
            tempEvent.start()
        elif state == spaStopping:
            self.shutdownSequence.setState(seqStart, wait=False)
            stopEvent = EventThread("spaStopping", self.shutdownSequence.getState, seqStopped, self.setState, spaOff)
            stopEvent.start()
        self.state = state

class EventThread(threading.Thread):
    def __init__(self, name, checkFunction, checkValue, actionFunction, actionValue):
        threading.Thread.__init__(self, target=self.asyncEvent)
        self.name = name
        self.checkFunction = checkFunction
        self.checkValue = checkValue
        self.actionFunction = actionFunction
        self.actionValue = actionValue

    def asyncEvent(self):
    # wait for the state of the specified sensor to reach the specified check value
    # then call the specified action function with the specified action value
        if debugThread: log(self.name, "started")
        while self.checkFunction() != self.checkValue:
            time.sleep(1)
        self.actionFunction(self.actionValue)
        if debugThread: log(self.name, "terminated")
