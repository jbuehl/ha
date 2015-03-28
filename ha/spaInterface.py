import json
import time
import threading
import requests
import urllib
from ha.HAClasses import *
from twilio.rest import TwilioRestClient

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

# get the value of a variable from a file
def getValue(fileName):
    return json.load(open(fileName))
    
# send an sms notification
def smsNotify(numbers, message):
    smsClient = TwilioRestClient(getValue(smsSid), getValue(smsToken))
    smsFrom = getValue(notifyFromNumber)
    for smsTo in getValue(numbers):
        smsClient.sms.messages.create(to=smsTo, from_=smsFrom, body=message)

# send an iOS app notification
def iosNotify(app, message):
    requests.get("http://"+app+".appspot.com/notify?message="+urllib.quote(message))
    
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
                              HACycle(self.heaterControl, duration=0, startState=on, delay=10)
                              ])
        self.onSequence = HASequence("spaOn", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMax),
#                              HACycle(self.lightControl, duration=0, startState=on)
                              ])
        self.standbySequence = HASequence("spaStandby", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMed),
#                              HACycle(self.lightControl, duration=0, startState=on)
                              ])
        self.shutdownSequence = HASequence("spaShutdown", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMed),
                              HACycle(self.heaterControl, duration=0, startState=off),
                              HACycle(self.pumpControl, duration=0, startState=off, delay=300),
                              HACycle(self.valveControl, duration=0, startState=valvesPool),
                              HACycle(self.lightControl, duration=0, startState=off, delay=30)
                              ])

    def read(self, addr):
        if addr == 0:
            return self.state
        else:
            return self.tempSensor.getState()

    # Implements the state diagram
    def write(self, addr, value):
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

    # Implements state transitions
    def setState(self, state, endState=None):
        if debugState: log(self.name, "setState ", state)
        if state == spaOn:
            self.onSequence.setState(seqStart, wait=True)
        elif state == spaStandby:
            self.standbySequence.setState(seqStart, wait=True)
        elif state == spaStarting:
            self.startupSequence.setState(seqStart, wait=False)
            startEvent = EventThread("spaStarting", self.startupSequence.getState, seqStopped, self.spaStarted, endState)
            startEvent.start()
        elif state == spaStopping:
            self.shutdownSequence.setState(seqStart, wait=False)
            stopEvent = EventThread("spaStopping", self.shutdownSequence.getState, seqStopped, self.setState, spaOff)
            stopEvent.start()
        self.state = state

    # called when startup sequence is complete
    def spaStarted(self, endState):
        self.setState(spaWarming)
        tempEvent = EventThread("spaWarming", self.tempSensor.getState, spaTempTarget, self.spaReady, endState)
        tempEvent.start()

    # called when target temperature is reached        
    def spaReady(self, state):
        self.setState(state)
        smsNotify(spaReadyNotifyNumbers, "Spa is ready")
        iosNotify("shadyglade-app", "Spa is ready")
        
# start a thread to wait for the state of the specified sensor to reach the specified value
# then call the specified action function with the specified action value
class EventThread(threading.Thread):
    def __init__(self, name, checkFunction, checkValue, actionFunction, actionValue):
        threading.Thread.__init__(self, target=self.asyncEvent)
        self.name = name
        self.checkFunction = checkFunction
        self.checkValue = checkValue
        self.actionFunction = actionFunction
        self.actionValue = actionValue

    def asyncEvent(self):
        if debugThread: log(self.name, "started")
        while self.checkFunction() != self.checkValue:
            time.sleep(1)
        self.actionFunction(self.actionValue)
        if debugThread: log(self.name, "terminated")

