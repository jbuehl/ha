
import threading
import time
from ha.HAClasses import *
from ha.serialInterface import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.pentairInterface import *
from ha.powerInterface import *
from ha.spaInterface import *
from ha.restServer import *
from ha.ADS1015Interface import *
from ha.analogTempInterface import *
from ha.valveInterface import *
#from ha.timeInterface import *

serial1Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}

heaterOff = 0
heaterOn = 1
heaterEnabled = 4

# a temperature controlled heater
class HeaterControl(HAControl):
    def __init__(self, name, interface, heaterControl, tempSensor, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.className = "HAControl"
        self.heaterControl = heaterControl      # the heater
        self.tempSensor = tempSensor          # the temp sensor
        self.tempTarget = 0
        self.currentState = heaterOff

    def getState(self, wait=False):
        debug('debugState', self.name, "getState ", self.currentState)
        return self.currentState

    def setState(self, state, wait=False):
        debug('debugState', self.name, "setState ", state)
        # thread to monitor the temperature
        def tempWatch():
            debug('debugHeater', self.name, "tempWatch started")
            while self.currentState != heaterOff:  # stop when state is set to off
                time.sleep(1)
                if self.currentState == heaterOff:
                    debug('debugHeater', self.name, "heater off")
                    self.heaterControl.setState(heaterOff)
                elif self.currentState == heaterOn:
                    if self.tempSensor.getState() >= self.tempTarget + self.hysteresis:
                        if self.heaterControl.getState() != heaterOff:
                            self.heaterControl.setState(heaterOff)
                            self.currentState = heaterEnabled
                            debug('debugHeater', self.name, "heater enabled")
                    else:
                        if self.heaterControl.getState() != heaterOn:
                            self.heaterControl.setState(heaterOn)
                            self.currentState = heaterOn
                            debug('debugHeater', self.name, "heater on")
                elif self.currentState == heaterEnabled:
                    if self.tempSensor.getState() <= self.tempTarget - self.hysteresis:
                        self.heaterControl.setState(heaterOn)
                        self.currentState = heaterOn
                        debug('debugHeater', self.name, "heater on")
                else:
                    debug('debugHeater', self.name, "unknown state", self.currentState)                    
            debug('debugHeater', self.name, "tempWatch terminated")
        if state != heaterOn:           # only allow explicit set on or off
            state = heaterOff
        else:
            if self.currentState == heaterOn:   # ignore multiple sets to on
                return
        self.currentState = state
        if self.currentState == heaterOn:      # start the monitor thread when state set to on
            tempWatchThread = threading.Thread(target=tempWatch)
            tempWatchThread.start()
        self.notify()

    def setTarget(self, tempTarget, hysteresis=1, wait=False):
        debug('debugHeater', self.name, "setTarget ", tempTarget, hysteresis)
        self.tempTarget = tempTarget
        self.hysteresis = hysteresis

# control that can only be turned on if all the specified resources are in the specified states
class DependentControl(HAControl):
    def __init__(self, name, interface, control, resources, addr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
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
    serial1 = HASerialInterface("Serial1", device="/dev/ttyAMA0", config=serial1Config, event=stateChangeEvent)
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
    heater = HAControl("heater", gpio1, 2, group="Pool", label="Heater", type="heater")
    spaHeater = HeaterControl("spaHeater", nullInterface, heater, waterTemp, group="Pool", label="Heater", type="heater")
    spaHeater.setTarget(spaTempTarget)
    spaBlower = HAControl("spaBlower", gpio0, 1, group="Pool", label="Blower")
    
    resources.addRes(poolPump)
    resources.addRes(HASensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed"))
    resources.addRes(HASensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow"))
    resources.addRes(poolCleaner)
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
    spaInterface = SpaInterface("SpaInterface", valveMode, poolPump, spaHeater, spaLight, waterTemp)
    spa = HAControl("spa", spaInterface, 0, group="Pool", label="Spa", type="spa")
    spa1 = HAControl("spa1", spaInterface, 1, group="Pool", label="Spa", type="spaTemp")
    spaLightNight = DependentControl("spaLightNight", nullInterface, spaLight, [(spa, 1)])
    resources.addRes(spa)
    resources.addRes(spa1)
    
    resources.addRes(HASequence("filter", [HACycle(poolPump, duration=39600, startState=1),  # filter 11 hr
                                              ], group="Pool", label="Filter daily"))
    resources.addRes(HASequence("clean", [HACycle(poolCleaner, duration=3600, startState=1), 
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
    schedule.addTask(HATask("Pool cleaner", HASchedTime(hour=[8], minute=[0]), resources["clean"], 1))
    schedule.addTask(HATask("Flush spa", HASchedTime(hour=[8], minute=[1]), resources["flush"], 1))
    schedule.addTask(HATask("Spa light on sunset", HASchedTime(event="sunset"), spaLightNight, 1))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    pentairInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Pool")
    restServer.start()

