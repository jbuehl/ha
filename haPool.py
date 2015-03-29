from ha.HAClasses import *
from ha.serialInterface import *
from ha.aqualinkInterface import *
from ha.pentairInterface import *
from ha.powerInterface import *
from ha.spaInterface import *
from ha.restServer import *
from ha.timeInterface import *

# Force usb serial devices to associate with specific devices based on which port they are plugged into

# cat >> /etc/udev/rules.d/91-local.rules << ^D
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.1", NAME="ttyUSB0", SYMLINK+="aqualink"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.2", NAME="ttyUSB1", SYMLINK+="pentair"
# KERNEL=="ttyUSB*", KERNELS=="1-1.2.3", NAME="ttyUSB2", SYMLINK+="x10"
# ^D

serial0Config = {"baudrate": 9600, 
                 "bytesize": serial.EIGHTBITS, 
                 "parity": serial.PARITY_NONE, 
                 "stopbits": serial.STOPBITS_ONE}
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
        if debugState: log(self.name, "setState ", theState)
        for sensor in self.resources:
            if debugSpaLight: log(self.name, sensor[0].name, sensor[0].getState())
            if sensor[0].getState() != sensor[1]:
                return
        self.control.setState(theState)

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    schedule = HASchedule("schedule")
    resources.addRes(schedule)

    # Interfaces
    stateChangeEvent = threading.Event()
    nullInterface = HAInterface("Null", HAInterface("None"))
    serial0 = HASerialInterface("Serial0", device=aqualinkDevice, config=serial0Config, event=stateChangeEvent)
    serial1 = HASerialInterface("Serial1", device=pentairDevice, config=serial1Config, event=stateChangeEvent)
    aqualinkInterface = AqualinkInterface("Aqualink", serial0)
    pentairInterface = PentairInterface("Pentair", serial1)
    powerInterface = HAPowerInterface("Power", HAInterface("None"), event=stateChangeEvent)
#    timeInterface = TimeInterface("Time")
    
    # Lights
    poolLight = HAControl("poolLight", aqualinkInterface, "aux4", type="light", group="Lights", label="Pool light")
    spaLight = HAControl("spaLight", aqualinkInterface, "aux5", type="light", group="Lights", label="Spa light")
    resources.addRes(poolLight)
    resources.addRes(spaLight)
    resources.addRes(HAScene("poolLights", [resources["poolLight"], 
                                          resources["spaLight"]], type="light", group="Lights", label="Pool and spa"))

    # Temperature
    airTemp = HASensor("airTemp", aqualinkInterface, "airTemp", "Temperature",label="Air temp", type="tempF")
    poolTemp = HASensor("poolTemp", aqualinkInterface, "poolTemp", "Temperature", label="Pool temp", type="tempF")
    spaTemp = HASensor("spaTemp", aqualinkInterface, "spaTemp", "Temperature", label="Spa temp", type="spaTemp")
    resources.addRes(airTemp)
    resources.addRes(poolTemp)
    resources.addRes(spaTemp)

    # Pool
    poolPump = HAControl("poolPump", pentairInterface, 0, group="Pool", label="Pump", type="pump")
    poolCleaner = HAControl("poolCleaner", aqualinkInterface, "aux1", group="Pool", label="Polaris", type="cleaner")
    poolValves = HAControl("poolValves", aqualinkInterface, "spa", group="Pool", label="Valves", type="poolValves")
    spaHeater = HAControl("spaHeater", aqualinkInterface, "spaHtr", group="Pool", label="Heater", type="heater")
    spaBlower = HAControl("spaBlower", aqualinkInterface, "aux2", group="Pool", label="Blower")
    
#    resources.addRes(HAControl("Pool pump", aqualinkInterface, "pump", group="Pool"))
    resources.addRes(poolPump)
    resources.addRes(HASensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed"))
    resources.addRes(HASensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow"))
    resources.addRes(poolCleaner)
    resources.addRes(poolValves)
    resources.addRes(spaHeater)
    resources.addRes(spaBlower)
#    resources.addRes(HAHeaterControl("Pool heater", aqualinkInterface, "poolHtr", group="Pool"))
#    resources.addRes(HASensor("model", aqualinkInterface, "poolModel", group="Pool", label="Controller model"))
    resources.addRes(HASensor("poolDate", aqualinkInterface, "poolDate", group="Pool", label="Controller date"))
    resources.addRes(HASensor("poolTime", aqualinkInterface, "poolTime", group="Pool", label="Controller time"))

    # Spa
#    dayLight = HASensor("daylight", timeInterface, "daylight")
    spaInterface = SpaInterface("SpaInterface", poolValves, poolPump, spaHeater, spaLight, spaTemp)
    spa = HAControl("spa", spaInterface, 0, group="Pool", label="Spa", type="spa")
    spa1 = HAControl("spa1", spaInterface, 1, group="Pool", label="Spa", type="spaTemp")
    spaLightNight = DependentControl("spaLightNight", nullInterface, spaLight, [(spa, 1)])
    resources.addRes(spa)
    resources.addRes(spa1)
    resources.addRes(spaLightNight)
    
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
    schedule.addTask(HATask("Pool cleaning", HASchedTime(hour=[8], minute=[0]), resources["cleanMode"], 1))
    schedule.addTask(HATask("Spa light on sunset", HASchedTime(event="sunset"), resources["spaLightNight"], 1))

    # Start interfaces
    aqualinkInterface.start()
    pentairInterface.start()
    schedule.start()
    restServer = RestServer(resources, port=7379, event=stateChangeEvent)
    restServer.start()

