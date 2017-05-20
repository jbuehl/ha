spaTempTarget = 100
spaNotifyMsg = "Spa is ready"
notifyFromNumber = ""
spaReadyNotifyNumbers = []
spaReadyNotifyApp = ""

import threading
import time
import json
from ha import *
from ha.interfaces.serialInterface import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.pentairInterface import *
from ha.interfaces.powerInterface import *
from ha.restServer import *
from ha.interfaces.ads1015Interface import *
from ha.interfaces.analogTempInterface import *
from ha.interfaces.valveInterface import *
from ha.tempControl import *
from ha.interfaces.timeInterface import *
from ha.notify import *

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

valvePool = 0
valveSpa = 1
valveMoving = 4

class SpaControl(Control):
    def __init__(self, name, interface, valveControl, pumpControl, heaterControl, lightControl, tempSensor, addr=None, 
            group="", type="control", location=None, view=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "Control"
        self.currentState = spaOff
        self.valveControl = valveControl
        self.pumpControl = pumpControl
        self.heaterControl = heaterControl
        self.lightControl = lightControl
        self.tempSensor = tempSensor
        self.eventThread = None
        
        # state transition sequences
        self.startupSequence = Sequence("spaStartup", 
                             [Cycle(self.valveControl, duration=0, startState=valveSpa),
                              Cycle(self.pumpControl, duration=0, startState=pumpMed, delay=30),
                              Cycle(self.heaterControl, duration=0, startState=on, delay=30)
                              ])
        self.onSequence = Sequence("spaOn", 
                             [Cycle(self.pumpControl, duration=0, startState=pumpMax),
                              Cycle(self.lightControl, duration=0, startState=on),
                              ])
        self.standbySequence = Sequence("spaStandby", 
                             [Cycle(self.pumpControl, duration=0, startState=pumpMed),
                              Cycle(self.lightControl, duration=0, startState=off),
                              ])
        self.shutdownSequence = Sequence("spaShutdown", 
                             [Cycle(self.pumpControl, duration=0, startState=pumpMed),
                              Cycle(self.heaterControl, duration=0, startState=off),
                              Cycle(self.pumpControl, duration=0, startState=off, delay=60),
                              Cycle(self.valveControl, duration=0, startState=valvePool),
                              Cycle(self.lightControl, duration=0, startState=off, delay=30)
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
            self.startEventThread("spaStarting", self.startupSequence.getState, seqStopped, self.spaStarted, endState)
        elif state == spaStopping:
            self.shutdownSequence.setState(seqStart, wait=False)
            self.startEventThread("spaStopping", self.shutdownSequence.getState, seqStopped, self.stateTransition, spaOff)
        self.currentState = state

    # called when startup sequence is complete
    def spaStarted(self, endState):
        debug('debugState', self.name, "spaStarted ", endState)
        self.stateTransition(spaWarming)
        self.startEventThread("spaWarming", self.tempSensor.getState, spaTempTarget, self.spaReady, endState)

    # called when target temperature is reached        
    def spaReady(self, state):
        debug('debugState', self.name, "spaReady ", state)
        self.stateTransition(state)
        smsNotify(spaReadyNotifyNumbers, spaNotifyMsg)
        iosNotify(spaReadyNotifyApp, spaNotifyMsg)

    # start an event thread
    def startEventThread(self, name, checkFunction, checkValue, actionFunction, actionValue):
        if self.eventThread:
            self.eventThread.cancel()
            self.eventThread = None
        self.eventThread = EventThread(name, checkFunction, checkValue, actionFunction, actionValue)
        self.eventThread.start()
            
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
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        
    def asyncEvent(self):
        debug('debugThread', self.name, "started")
        while self.checkFunction() != self.checkValue:
            time.sleep(1)
            if self.cancelled:
                debug('debugThread', self.name, "cancelled")
                return
        self.actionFunction(self.actionValue)
        debug('debugThread', self.name, "finished")

# spa control whose state value includes the temperature
class SpaTempControl(Control):
    def __init__(self, name, interface, spaControl, tempSensor, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "Control"
        self.spaControl = spaControl
        self.tempSensor = tempSensor

    def getState(self):
        return "%d %d"%(self.tempSensor.getState(), self.spaControl.getState())

    def setState(self, state):
        self.spaControl.setState(state)
        
# control that can only be turned on if all the specified resources are in the specified states
class DependentControl(Control):
    def __init__(self, name, interface, control, resources, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "Control"
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
    resources = Collection("resources")
    schedule = Schedule("schedule")

    # Interfaces
    stateChangeEvent = threading.Event()
    nullInterface = Interface("Null", Interface("None"))
    serial1 = SerialInterface("Serial1", device=pentairDevice, config=serial1Config, event=stateChangeEvent)
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x20, bank=1, inOut=0x00)
    pentairInterface = PentairInterface("Pentair", serial1)
    powerInterface = PowerInterface("Power", Interface("None"), event=stateChangeEvent)
    ads1015Interface = ADS1015Interface("ADS1015", addr=0x48)
    analogTempInterface = AnalogTempInterface("AnalogTemp", ads1015Interface)
    valveInterface = ValveInterface("Valves", gpio1)
    timeInterface = TimeInterface("Time")
    
    # Lights
    poolLight = Control("poolLight", gpio0, 2, type="light", group="Lights", label="Pool light")
    spaLight = Control("spaLight", gpio0, 3, type="light", group="Lights", label="Spa light")
    resources.addRes(poolLight)
    resources.addRes(spaLight)
    resources.addRes(ControlGroup("poolLights", [poolLight, spaLight], type="light", group="Lights", label="Pool and spa"))

    # Temperature
    waterTemp = Sensor("waterTemp", analogTempInterface, 0, "Temperature",label="Water temp", type="tempF")
    poolEquipTemp = Sensor("poolEquipTemp", analogTempInterface, 1, "Temperature",label="Pool equipment temp", type="tempF")
    resources.addRes(waterTemp)
    resources.addRes(poolEquipTemp)

    # Pool
    poolPump = Control("poolPump", pentairInterface, 0, group="Pool", label="Pump", type="pump")
    poolCleaner = Control("poolCleaner", gpio0, 0, group="Pool", label="Polaris", type="cleaner")
    intakeValve = Control("intakeValve", valveInterface, 0, group="Pool", label="Intake valve", type="poolValve")
    returnValve = Control("returnValve", valveInterface, 1, group="Pool", label="Return valve", type="poolValve")
    valveMode = ControlGroup("valveMode", [intakeValve, returnValve], stateList=[[0, 1, 1, 0], [0, 1, 0, 1]], stateMode=True, 
                             type="valveMode", group="Pool", label="Valve mode")
    spaFill = ControlGroup("spaFill", [intakeValve, returnValve, poolPump], stateList=[[0, 0], [0, 1], [0, 4]], stateMode=True, group="Pool", label="Spa fill")
    spaFlush = ControlGroup("spaFlush", [intakeValve, returnValve, poolPump], stateList=[[0, 0], [0, 1], [0, 3]], stateMode=True, group="Pool", label="Spa flush")
    spaDrain = ControlGroup("spaDrain", [intakeValve, returnValve, poolPump], stateList=[[0, 1], [0, 0], [0, 4]], stateMode=True, group="Pool", label="Spa drain")
    poolClean = ControlGroup("poolClean", [poolCleaner, poolPump], stateList=[[0, 1], [0, 3]], stateMode=True, group="Pool", label="Pool clean")
    heater = Control("heater", gpio1, 2, group="Pool", label="Heater", type="heater")
    spaHeater = TempControl("spaHeater", nullInterface, heater, waterTemp, group="Pool", label="Heater", type="heater")
    spaHeater.setTarget(spaTempTarget)
    spaBlower = Control("spaBlower", gpio0, 1, group="Pool", label="Blower")
    
    resources.addRes(poolPump)
    resources.addRes(Sensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed"))
    resources.addRes(Sensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow"))
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
    sunUp = Sensor("sunUp", timeInterface, "sunUp")
    # spa light control that will only turn on if the sun is down
    spaLightNight = DependentControl("spaLightNight", nullInterface, spaLight, [(sunUp, 0)])
    spa = SpaControl("spa", nullInterface, valveMode, poolPump, spaHeater, spaLightNight, waterTemp, group="Pool", label="Spa", type="spa")
    spaTemp = SpaTempControl("spaTemp", nullInterface, spa, waterTemp, group="Pool", label="Spa", type="spaTemp")
    # spa light control that will only turn on if the sun is down and the spa is on
    spaLightNightSpa = DependentControl("spaLightNightSpa", nullInterface, spaLightNight, [(spa, 1)])
    resources.addRes(spa)
    resources.addRes(spaTemp)
    
    resources.addRes(Sequence("filter", [Cycle(poolPump, duration=39600, startState=1),  # filter 11 hr
                                              ], group="Pool", label="Filter daily"))
    resources.addRes(Sequence("clean", [Cycle(poolClean, duration=3600, startState=1), 
                                              ], group="Pool", label="Clean 1 hr"))
    resources.addRes(Sequence("flush", [Cycle(spaFlush, duration=900, startState=1), 
                                              ], group="Pool", label="Flush spa 15 min"))

    # Power
    resources.addRes(Sensor("poolPumpPower", pentairInterface, 2, type="power", group="Power", label="Pool pump"))
    resources.addRes(Sensor("poolCleanerPower", powerInterface, poolCleaner, type="power", group="Power", label="Pool cleaner"))
    resources.addRes(Sensor("spaBlowerPower", powerInterface, spaBlower, type="power", group="Power", label="Spa blower"))
    resources.addRes(Sensor("poolLightPower", powerInterface, poolLight, type="power", group="Power", label="Pool light"))
    resources.addRes(Sensor("spaLightPower", powerInterface, spaLight, type="power", group="Power", label="Spa light"))

    # Schedules
    resources.addRes(schedule)
    schedule.addTask(Task("Sunday spa on", SchedTime(year=[2016], month=[8], day=[14], hour=[16], minute=[30]), resources["spa"], 1))
    schedule.addTask(Task("Sunday spa off", SchedTime(year=[2016], month=[8], day=[14], hour=[18], minute=[30]), resources["spa"], 0))
    schedule.addTask(Task("Pool filter", SchedTime(hour=[21], minute=[0]), resources["filter"], 1))
    schedule.addTask(Task("Pool cleaner", SchedTime(hour=[8], minute=[1]), resources["clean"], 1))
    schedule.addTask(Task("Flush spa", SchedTime(hour=[9], minute=[2]), resources["flush"], 1))
    schedule.addTask(Task("Spa light on sunset", SchedTime(event="sunset"), spaLightNightSpa, 1))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    pentairInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Pool")
    restServer.start()

