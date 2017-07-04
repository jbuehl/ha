backHeatTempTargetDefault = 65
backCoolTempTargetDefault = 75
windSpeedAddr = 1
windDirAddr = 2

import threading
from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.owfsInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.tempInterface import *
from ha.interfaces.windInterface import *
from ha.controls.tempControl import *
from ha.controls.thermostatControl import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    nullInterface = Interface("nullInterface", event=stateChangeEvent)
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"backhouse.state", event=stateChangeEvent)
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("gpio0", i2c1, addr=0x20, bank=0, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])
    gpio1 = GPIOInterface("gpio1", i2c1, addr=0x20, bank=1, inOut=0x00)

    # Weather
    anemometer = Sensor("anemometer", gpio0, addr=windSpeedAddr)
    windVane = Sensor("windVane", gpio0, addr=windDirAddr)
    windInterface = WindInterface("windInterface", gpio0, anemometer=anemometer, windVane=windVane)
    windSpeed = Sensor("windSpeed", windInterface, addr="speed", type="MPH", group="Weather", label="Wind speed")
    windDir = Sensor("windDir", windInterface, addr="dir", type="Deg", group="Weather", label="Wind direction")
    
    # Doors
    backHouseDoor = Sensor("backHouseDoor", gpio0, 0, type="door", group=["Doors", "Hvac"], label="Back house")
    
    # persistent config data
    backHeatTempTarget = Control("backHeatTempTarget", configData, "backHeatTempTarget", group="Hvac", label="Back heat set", type="tempFControl")
    backCoolTempTarget = Control("backCoolTempTarget", configData, "backCoolTempTarget", group="Hvac", label="Back cool set", type="tempFControl")
    backThermostatMode = Control("backThermostatMode", configData, "backThermostatMode")
   
    # Temperature sensors
    backHouseTemp = Sensor("backHouseTemp", owfs, "28.746BDB060000", group=["Hvac", "Temperature"], label="Back house temp", type="tempF")
    
    # HVAC equipment controls
    backHeat = Control("backHeat", gpio1, 0, group="Hvac", label="Back heat")
    backCool = Control("backCool", gpio1, 1, group="Hvac", label="Back cool")
    backFan  = Control("backFan",  gpio1, 3, group="Hvac", label="Back fan")

    # Temp controls
    backHeatControl = TempControl("backHeatControl", nullInterface, 
                                    backHeat, backHouseTemp, backHeatTempTarget, unitType=unitTypeHeater, 
                                    group="Hvac", label="Back heat control", type="tempControl")
    backCoolControl = TempControl("backCoolControl", nullInterface, 
                                    backCool, backHouseTemp, backCoolTempTarget, unitType=unitTypeAc, 
                                    group="Hvac", label="Back cool control", type="tempControl")

    # Thermostats
    backThermostat = ThermostatControl("backThermostat",backHeatControl, backCoolControl, backFan, backHouseDoor, backThermostatMode,
                                    group="Hvac", label="Back thermostat", type="thermostat", event=stateChangeEvent)
    backThermostatUnitSensor = ThermostatUnitSensor("backThermostatUnitSensor", backThermostat,
                                    group="Hvac", label="Back thermostat unit", type="thermostatSensor")

    # Tasks
    backHeatTempUpMorning = Task("backHeatTempUpMorning", SchedTime(hour=[6], minute=[0]), backHeatTempTarget, 69)
    backHeatTempDownMorning = Task("backHeatTempDownMorning", SchedTime(hour=[8], minute=[0]), backHeatTempTarget, 66)
    backHeatTempDownEvening = Task("backHeatTempDownEvening", SchedTime(hour=[21], minute=[0]), backHeatTempTarget, 66)
    
    # Schedule
    schedule = Schedule("schedule", tasks=[backHeatTempUpMorning, backHeatTempDownMorning, backHeatTempDownEvening])

    # Resources
    resources = Collection("resources", resources=[windSpeed, windDir,
                                                   backHouseTemp, 
                                                   backHeat, backCool, backFan, backHeatTempTarget, backCoolTempTarget, 
                                                   backHeatControl, backCoolControl, backThermostat, backThermostatUnitSensor,
                                                   backHouseDoor, 
                                                   backHeatTempUpMorning, backHeatTempDownMorning, backHeatTempDownEvening,
                                                   ])
    restServer = RestServer(resources, event=stateChangeEvent, label="Back house")

    # Start interfaces
    configData.start()
    if not backHeatTempTarget.getState():
        backHeatTempTarget.setState(backHeatTempTargetDefault)
    if not backCoolTempTarget.getState():
        backCoolTempTarget.setState(backCoolTempTargetDefault)
    gpio0.start()
    gpio1.start()
    backThermostat.start()
    schedule.start()
    restServer.start()

