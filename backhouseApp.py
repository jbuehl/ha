defaultConfig = {
    "backHeatTempTarget": 65,
    "backCoolTempTarget": 75,
}

import threading
from ha import *
from ha.interfaces.mcp23017Interface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.owfsInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.tempInterface import *
from ha.controls.tempControl import *
from ha.controls.thermostatControl import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    nullInterface = Interface("nullInterface", event=stateChangeEvent)
    owfs = OWFSInterface("owfs")
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"backhouse.state", event=stateChangeEvent, initialState=defaultConfig)
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    gpio0 = MCP23017Interface("gpio0", i2c1, addr=0x20, bank=0, inOut=0xff, config=[(MCP23017Interface.IPOL, 0x00)])
    gpio1 = MCP23017Interface("gpio1", i2c1, addr=0x20, bank=1, inOut=0x00)

    # Doors
    backHouseDoor = Sensor("backHouseDoor", gpio0, 0, type="door", group=["Doors", "Hvac"], label="Back house")

    # persistent config data
    backHeatTempTarget = Control("backHeatTempTarget", fileInterface, "backHeatTempTarget", group="Hvac", label="Back heat set", type="tempFControl")
    backCoolTempTarget = Control("backCoolTempTarget", fileInterface, "backCoolTempTarget", group="Hvac", label="Back cool set", type="tempFControl")
    backThermostatMode = Control("backThermostatMode", fileInterface, "backThermostatMode")

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
                                    group="Hvac", label="Back thermostat", type="thermostat")
    backThermostatUnitSensor = ThermostatUnitSensor("backThermostatUnitSensor", backThermostat,
                                    group="Hvac", label="Back thermostat unit", type="thermostatSensor")

    # Tasks
    backHeatTempUpMorning = Task("backHeatTempUpMorning", SchedTime(hour=[6], minute=[0]), backHeatTempTarget, 69, enabled=False)
    backHeatTempDownMorning = Task("backHeatTempDownMorning", SchedTime(hour=[8], minute=[0]), backHeatTempTarget, 66, enabled=False)
    backHeatTempDownEvening = Task("backHeatTempDownEvening", SchedTime(hour=[21], minute=[0]), backHeatTempTarget, 66, enabled=False)

    # Schedule
    schedule = Schedule("schedule", tasks=[backHeatTempUpMorning, backHeatTempDownMorning, backHeatTempDownEvening])

    # Resources
    resources = Collection("resources", resources=[backHouseTemp,
                                                   backHeat, backCool, backFan, backHeatTempTarget, backCoolTempTarget,
                                                   backHeatControl, backCoolControl, backThermostat, backThermostatUnitSensor,
                                                   backHouseDoor,
                                                   backHeatTempUpMorning, backHeatTempDownMorning, backHeatTempDownEvening,
                                                   ], event=stateChangeEvent)
    restServer = RestServer("backhouse", resources, event=stateChangeEvent, label="Back house")

    # Start interfaces
    fileInterface.start()
    gpio0.start()
    gpio1.start()
    backThermostat.start()
    schedule.start()
    restServer.start()
