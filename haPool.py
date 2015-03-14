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

# control that can only be turned on if all the specified sensors are in the specified states
class DependentControl(HAControl):
    def __init__(self, theName, theInterface, control, sensors, theAddr=None, group="", type="control", location=None, view=None, label="", interrupt=None):
        HAControl.__init__(self, theName, theInterface, theAddr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.control = control
        self.sensors = sensors

    def setState(self, theState, wait=False):
        if debugState: log(self.name, "setState ", theState)
        for sensor in self.sensors:
            if debugSpaLight: log(self.name, sensor[0].name, sensor[0].getState())
            if sensor[0].getState() != sensor[1]:
                return
        self.control.setState(theState)

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    nullInterface = HAInterface("Null", HAInterface("None"))
    serial0 = HASerialInterface("Serial0", aqualinkDevice, serial0Config)
    serial1 = HASerialInterface("Serial1", pentairDevice, serial1Config)
    aqualinkInterface = AqualinkInterface("Aqualink", serial0)
    pentairInterface = PentairInterface("Pentair", serial1)
    powerInterface = HAPowerInterface("Power", HAInterface("None"), powerTbl)
#    timeInterface = TimeInterface("Time")
    
    sensors.addRes(HAControl("Null", nullInterface, None))
    
    # Lights
    poolLight = HAControl("poolLight", aqualinkInterface, "aux4", type="light", group="Lights", label="Pool light")
    spaLight = HAControl("spaLight", aqualinkInterface, "aux5", type="light", group="Lights", label="Spa light")
    sensors.addRes(poolLight)
    sensors.addRes(spaLight)
    sensors.addRes(HAScene("poolLights", [sensors["poolLight"], 
                                          sensors["spaLight"]], type="light", group="Lights", label="Pool and spa"))

    # Temperature
    airTemp = HASensor("airTemp", aqualinkInterface, "airTemp", "Temperature",label="Air temp", type="tempF")
    poolTemp = HASensor("poolTemp", aqualinkInterface, "poolTemp", "Temperature", label="Pool temp", type="tempF")
    spaTemp = HASensor("spaTemp", aqualinkInterface, "spaTemp", "Temperature", label="Spa temp", type="tempF")
    sensors.addRes(airTemp)
    sensors.addRes(poolTemp)
    sensors.addRes(spaTemp)

    # Pool
    poolPump = HAControl("poolPump", pentairInterface, 0, group="Pool", label="Pump", type="pump")
    poolCleaner = HAControl("poolCleaner", aqualinkInterface, "aux1", group="Pool", label="Polaris", type="cleaner")
    poolValves = HAControl("poolValves", aqualinkInterface, "spa", group="Pool", label="Valves", type="poolValves")
    spaHeater = HAControl("spaHeater", aqualinkInterface, "spaHtr", group="Pool", label="Heater", type="heater")
    spaBlower = HAControl("spaBlower", aqualinkInterface, "aux2", group="Pool", label="Blower")
    
#    sensors.addRes(HAControl("Pool pump", aqualinkInterface, "pump", group="Pool"))
    sensors.addRes(poolPump)
    sensors.addRes(HASensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed"))
    sensors.addRes(HASensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow"))
    sensors.addRes(poolCleaner)
    sensors.addRes(poolValves)
    sensors.addRes(spaHeater)
    sensors.addRes(spaBlower)
#    sensors.addRes(HAHeaterControl("Pool heater", aqualinkInterface, "poolHtr", group="Pool"))
#    sensors.addRes(HASensor("model", aqualinkInterface, "model", group="Pool", label="Controller model"))
    sensors.addRes(HASensor("date", aqualinkInterface, "date", group="Pool", label="Controller date"))
    sensors.addRes(HASensor("time", aqualinkInterface, "time", group="Pool", label="Controller time"))

    # Spa
#    dayLight = HASensor("daylight", timeInterface, "daylight")
    spaInterface = SpaInterface("SpaInterface", poolValves, poolPump, spaHeater, spaLight, spaTemp)
    spa = HAControl("spa", spaInterface, None, group="Pool", label="Spa", type="spa")
    spaLightNight = DependentControl("spaLightNight", None, spaLight, [(spa, 1)])
    sensors.addRes(spa)
    sensors.addRes(spaLightNight)
    
    sensors.addRes(HASequence("cleanMode", [HACycle(sensors["poolPump"], duration=3600, startState=3), 
                                              HACycle(sensors["poolPump"], duration=0, startState=0)
                                              ], group="Pool", label="Clean mode"))
    sensors.addRes(HASequence("clean1hr", [HACycle(sensors["poolCleaner"], duration=3600, startState=1), 
                                              ], group="Pool", label="Clean 1 hr"))

    # Power
    sensors.addRes(HASensor("poolPumpPower", pentairInterface, 2, type="power", group="Power", label="Pool pump"))
    sensors.addRes(HASensor("poolCleanerPower", powerInterface, sensors["poolCleaner"], type="power", group="Power", label="Pool cleaner"))
    sensors.addRes(HASensor("spaBlowerPower", powerInterface, sensors["spaBlower"], type="power", group="Power", label="Spa blower"))
    sensors.addRes(HASensor("poolLightPower", powerInterface, sensors["poolLight"], type="power", group="Power", label="Pool light"))
    sensors.addRes(HASensor("spaLightPower", powerInterface, sensors["spaLight"], type="power", group="Power", label="Spa light"))

    # Schedules
    schedule.addTask(HATask("Pool cleaning", HASchedTime(hour=[8], minute=[0]), sensors["cleanMode"], 1))
    schedule.addTask(HATask("Spa light on sunset", HASchedTime(event="sunset"), spaLightNight, 1))

    # Start interfaces
    aqualinkInterface.start()
    pentairInterface.start()
    schedule.start()
    restServer = RestServer(resources, 7379)
    restServer.start()

