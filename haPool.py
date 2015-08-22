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
#from ha.timeInterface import *

serial1Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}

# control that can only be turned on if all the specified resources are in the specified states
class DependentControl(HAControl):
    def __init__(self, theName, theInterface, control, resources, theAddr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, theName, theInterface, theAddr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.control = control
        self.resources = resources

    def setState(self, theState, wait=False):
        debug('debugState', self.name, "setState ", theState)
        for sensor in self.resources:
            debug('debugSpaLight', self.name, sensor[0].name, sensor[0].getState())
            if sensor[0].getState() != sensor[1]:
                return
        self.control.setState(theState)

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
    intakeValve = HAControl("intakeValve", gpio1, 0, group="Pool", label="Intake valve", type="poolValves")
    returnValve = HAControl("returnValve", gpio1, 1, group="Pool", label="Return valve", type="poolValves")
    valveMode = HAScene("valveMode", [intakeValve, returnValve], stateList=[[0, 1, 1, 0], [0, 1, 0, 1]], type="valveMode", group="Pool", label="Valve mode")
    spaHeater = HAControl("spaHeater", gpio1, 2, group="Pool", label="Heater", type="heater")
    spaBlower = HAControl("spaBlower", gpio0, 1, group="Pool", label="Blower")
    
    resources.addRes(poolPump)
    resources.addRes(HASensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed"))
    resources.addRes(HASensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow"))
    resources.addRes(poolCleaner)
    resources.addRes(intakeValve)
    resources.addRes(returnValve)
    resources.addRes(valveMode)
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
#    resources.addRes(spaLightNight)
    
    resources.addRes(HASequence("cleanMode", [HACycle(resources["poolPump"], duration=3600, startState=3), 
                                              HACycle(resources["poolPump"], duration=0, startState=0)
                                              ], group="Pool", label="Clean mode"))
    resources.addRes(HASequence("clean1hr", [HACycle(resources["poolCleaner"], duration=3600, startState=1), 
                                              ], group="Pool", label="Clean 1 hr"))

    # Power
    resources.addRes(HASensor("poolPumpPower", pentairInterface, 2, type="power", group="Power", label="Pool pump"))
    resources.addRes(HASensor("poolCleanerPower", powerInterface, resources["poolCleaner"], type="power", group="Power", label="Pool cleaner"))
    resources.addRes(HASensor("spaBlowerPower", powerInterface, resources["spaBlower"], type="power", group="Power", label="Spa blower"))
    resources.addRes(HASensor("poolLightPower", powerInterface, resources["poolLight"], type="power", group="Power", label="Pool light"))
    resources.addRes(HASensor("spaLightPower", powerInterface, resources["spaLight"], type="power", group="Power", label="Spa light"))

    # Schedules
    resources.addRes(schedule)
    schedule.addTask(HATask("Pool cleaning", HASchedTime(hour=[8], minute=[0]), resources["clean1hr"], 1))
    schedule.addTask(HATask("Spa light on sunset", HASchedTime(event="sunset"), spaLightNight, 1))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    pentairInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Pool")
    restServer.start()

