spaTempTarget = 100
spaNotifyMsg = "Spa is ready"
notifyFromNumber = ""
spaReadyNotifyNumbers = []
spaReadyNotifyApp = ""

import threading
import time
import json
import requests
import urllib
from twilio.rest import TwilioRestClient
from ha.HAClasses import *
from ha.serialInterface import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.pentairInterface import *
from ha.powerInterface import *
from ha.restServer import *
from ha.ADS1015Interface import *
from ha.analogTempInterface import *
from ha.valveInterface import *
from ha.tempControl import *
#from ha.timeInterface import *

serial1Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}

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
    smsFrom = notifyFromNumber
    for smsTo in numbers:
        smsClient.sms.messages.create(to=smsTo, from_=smsFrom, body=message)

# send an iOS app notification
def iosNotify(app, message):
    if app != "":
        requests.get("http://"+app+".appspot.com/notify?message="+urllib.quote(message))
    
class SpaControl(HAControl):
    def __init__(self, name, interface, valveControl, pumpControl, heaterControl, lightControl, tempSensor, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "HAControl"
        self.currentState = spaOff
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
                              HACycle(self.lightControl, duration=0, startState=on),
                              ])
        self.standbySequence = HASequence("spaStandby", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMed),
                              HACycle(self.lightControl, duration=0, startState=off),
                              ])
        self.shutdownSequence = HASequence("spaShutdown", 
                             [HACycle(self.pumpControl, duration=0, startState=pumpMed),
                              HACycle(self.heaterControl, duration=0, startState=off),
                              HACycle(self.pumpControl, duration=0, startState=off, delay=60),
                              HACycle(self.valveControl, duration=0, startState=valvesPool),
                              HACycle(self.lightControl, duration=0, startState=off, delay=30)
                              ])

    def getState(self):
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
                self.stateTransition(spaStarting, spaOn)
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
            self.onSequence.setState(seqStart, wait=True)
        elif state == spaStandby:
            self.standbySequence.setState(seqStart, wait=True)
        elif state == spaStarting:
            self.startupSequence.setState(seqStart, wait=False)
            startEvent = EventThread("spaStarting", self.startupSequence.getState, seqStopped, self.spaStarted, endState)
            startEvent.start()
        elif state == spaStopping:
            self.shutdownSequence.setState(seqStart, wait=False)
            stopEvent = EventThread("spaStopping", self.shutdownSequence.getState, seqStopped, self.stateTransition, spaOff)
            stopEvent.start()
        self.currentState = state

    # called when startup sequence is complete
    def spaStarted(self, endState):
        debug('debugState', self.name, "spaStarted ", endState)
        self.stateTransition(spaWarming)
        tempEvent = EventThread("spaWarming", self.tempSensor.getState, spaTempTarget, self.spaReady, endState)
        tempEvent.start()

    # called when target temperature is reached        
    def spaReady(self, state):
        debug('debugState', self.name, "spaReady ", state)
        self.stateTransition(state)
        smsNotify(spaReadyNotifyNumbers, spaNotifyMsg)
        iosNotify(spaReadyNotifyApp, spaNotifyMsg)
        
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
        debug('debugThread', self.name, "started")
        while self.checkFunction() != self.checkValue:
            time.sleep(1)
        self.actionFunction(self.actionValue)
        debug('debugThread', self.name, "terminated")

# spa control whose state value includes the temperature
class SpaTempControl(HAControl):
    def __init__(self, name, interface, spaControl, tempSensor, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "HAControl"
        self.spaControl = spaControl
        self.tempSensor = tempSensor

    def getState(self):
        return "%d %d"%(self.tempSensor.getState(), self.spaControl.getState())

    def setState(self, state):
        self.spaControl.setState(state)
        
# control that can only be turned on if all the specified resources are in the specified states
class DependentControl(HAControl):
    def __init__(self, name, interface, control, resources, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "HAControl"
        self.control = control
        self.resources = resources

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        for sensor in self.resources:
            debug('debugSpaLight', self.name, sensor[0].name, sensor[0].getState())
            if sensor[0].getState() != sensor[1]:
                return
        self.control.setState(state)

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    schedule = HASchedule("schedule")

    # Interfaces
    stateChangeEvent = threading.Event()
    nullInterface = HAInterface("Null", HAInterface("None"))
    serial1 = HASerialInterface("Serial1", device=pentairDevice, config=serial1Config, event=stateChangeEvent)
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x20, bank=1, inOut=0x00)
    pentairInterface = PentairInterface("Pentair", serial1)
    powerInterface = HAPowerInterface("Power", HAInterface("None"), event=stateChangeEvent)
    ads1015Interface = ADS1015Interface("ADS1015", addr=0x48)
    analogTempInterface = AnalogTempInterface("AnalogTemp", ads1015Interface)
    valveInterface = ValveInterface("Valves", gpio1)
#    timeInterface = TimeInterface("Time")
    
    # Lights
    poolLight = HAControl("poolLight", gpio0, 2, type="light", group="Lights", label="Pool light")
    spaLight = HAControl("spaLight", gpio0, 3, type="light", group="Lights", label="Spa light")
    resources.addRes(poolLight)
    resources.addRes(spaLight)
    resources.addRes(HAScene("poolLights", [poolLight, spaLight], type="light", group="Lights", label="Pool and spa"))

    # Temperature
    waterTemp = HASensor("waterTemp", analogTempInterface, 0, "Temperature",label="Water temp", type="tempF")
    poolEquipTemp = HASensor("poolEquipTemp", analogTempInterface, 1, "Temperature",label="Pool equipment temp", type="tempF")
    resources.addRes(waterTemp)
    resources.addRes(poolEquipTemp)

    # Pool
    poolPump = HAControl("poolPump", pentairInterface, 0, group="Pool", label="Pump", type="pump")
    poolCleaner = HAControl("poolCleaner", gpio0, 0, group="Pool", label="Polaris", type="cleaner")
    intakeValve = HAControl("intakeValve", valveInterface, 0, group="Pool", label="Intake valve", type="poolValve")
    returnValve = HAControl("returnValve", valveInterface, 1, group="Pool", label="Return valve", type="poolValve")
    valveMode = HAScene("valveMode", [intakeValve, returnValve], stateList=[[0, 1, 1, 0], [0, 1, 0, 1]], type="valveMode", group="Pool", label="Valve mode")
    spaFill = HAScene("spaFill", [intakeValve, returnValve, poolPump], stateList=[[0, 0], [0, 1], [0, 4]], group="Pool", label="Spa fill")
    spaFlush = HAScene("spaFlush", [intakeValve, returnValve, poolPump], stateList=[[0, 0], [0, 1], [0, 3]], group="Pool", label="Spa flush")
    spaDrain = HAScene("spaDrain", [intakeValve, returnValve, poolPump], stateList=[[0, 1], [0, 0], [0, 4]], group="Pool", label="Spa drain")
    poolClean = HAScene("poolClean", [poolCleaner, poolPump], stateList=[[0, 1], [0, 3]], group="Pool", label="Pool clean")
    heater = HAControl("heater", gpio1, 2, group="Pool", label="Heater", type="heater")
    spaHeater = TempControl("spaHeater", nullInterface, heater, waterTemp, group="Pool", label="Heater", type="heater")
    spaHeater.setTarget(spaTempTarget)
    spaBlower = HAControl("spaBlower", gpio0, 1, group="Pool", label="Blower")
    
    resources.addRes(poolPump)
    resources.addRes(HASensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed"))
    resources.addRes(HASensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow"))
    resources.addRes(poolCleaner)
    resources.addRes(poolClean)
    resources.addRes(intakeValve)
    resources.addRes(returnValve)
    resources.addRes(valveMode)
    resources.addRes(spaFill)
    resources.addRes(spaFlush)
    resources.addRes(spaDrain)
    resources.addRes(spaHeater)
    resources.addRes(spaBlower)

    # Spa
#    dayLight = HASensor("daylight", timeInterface, "daylight")
    spa = SpaControl("spa", nullInterface, valveMode, poolPump, spaHeater, spaLight, waterTemp, group="Pool", label="Spa", type="spa")
    spaTemp = SpaTempControl("spaTemp", nullInterface, spa, waterTemp, group="Pool", label="Spa", type="spaTemp")
    spaLightNight = DependentControl("spaLightNight", nullInterface, spaLight, [(spa, 1)])
    resources.addRes(spa)
    resources.addRes(spaTemp)
    
    resources.addRes(HASequence("filter", [HACycle(poolPump, duration=39600, startState=1),  # filter 11 hr
                                              ], group="Pool", label="Filter daily"))
    resources.addRes(HASequence("clean", [HACycle(poolClean, duration=3600, startState=1), 
                                              ], group="Pool", label="Clean 1 hr"))
    resources.addRes(HASequence("flush", [HACycle(spaFlush, duration=900, startState=1), 
                                              ], group="Pool", label="Flush spa 15 min"))

    # Power
    resources.addRes(HASensor("poolPumpPower", pentairInterface, 2, type="power", group="Power", label="Pool pump"))
    resources.addRes(HASensor("poolCleanerPower", powerInterface, poolCleaner, type="power", group="Power", label="Pool cleaner"))
    resources.addRes(HASensor("spaBlowerPower", powerInterface, spaBlower, type="power", group="Power", label="Spa blower"))
    resources.addRes(HASensor("poolLightPower", powerInterface, poolLight, type="power", group="Power", label="Pool light"))
    resources.addRes(HASensor("spaLightPower", powerInterface, spaLight, type="power", group="Power", label="Spa light"))

    # Schedules
    resources.addRes(schedule)
    schedule.addTask(HATask("Pool filter", HASchedTime(hour=[21], minute=[0]), resources["filter"], 1))
    schedule.addTask(HATask("Pool cleaner", HASchedTime(hour=[8], minute=[1]), resources["clean"], 1))
    schedule.addTask(HATask("Flush spa", HASchedTime(hour=[9], minute=[2]), resources["flush"], 1))
    schedule.addTask(HATask("Spa light on sunset", HASchedTime(event="sunset"), spaLightNight, 1))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    pentairInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Pool")
    restServer.start()

