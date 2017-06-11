northHeatTempTargetDefault = 65
northCoolTempTargetDefault = 75
southHeatTempTargetDefault = 65
southCoolTempTargetDefault = 75

import threading
from ha import *
from ha.interfaces.gpioInterface import *
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
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"hvac.conf", event=stateChangeEvent)
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("gpio0", i2c1, addr=0x20, bank=0, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])
    gpio1 = GPIOInterface("gpio1", i2c1, addr=0x20, bank=1, inOut=0x00)

    # Doors
    frontDoor = Sensor("frontDoor", gpio0, 5, type="door", group="Doors", label="Front")
    familyRoomDoor = Sensor("familyRoomDoor", gpio0, 6, type="door", group="Doors", label="Family room")
    masterBedroomDoor = Sensor("masterBedroomDoor", gpio0, 7, type="door", group="Doors", label="Master bedroom")
    houseDoors = SensorGroup("houseDoors", [frontDoor, familyRoomDoor, masterBedroomDoor], type="door", group="Doors", label="House doors")
    
    # persistent config data
    northHeatTempTarget = Control("northHeatTempTarget", configData, "northHeatTempTarget", group="Hvac", label="North heat set", type="tempFControl")
    northCoolTempTarget = Control("northCoolTempTarget", configData, "northCoolTempTarget", group="Hvac", label="North cool set", type="tempFControl")
    northThermostatMode = Control("northThermostatMode", configData, "northThermostatMode")
    southHeatTempTarget = Control("southHeatTempTarget", configData, "southHeatTempTarget", group="Hvac", label="South heat set", type="tempFControl")
    southCoolTempTarget = Control("southCoolTempTarget", configData, "southCoolTempTarget", group="Hvac", label="South cool set", type="tempFControl")
    southThermostatMode = Control("southThermostatMode", configData, "southThermostatMode")
   
    # Temperature sensors
    masterBedroomTemp = Sensor("masterBedroomTemp", owfs, "28.175CDC060000", group=["Hvac", "Temperature"], label="Master bedroom temp", type="tempF")
    diningRoomTemp = Sensor("diningRoomTemp", owfs, "28.E4F6DB060000", group=["Hvac", "Temperature"], label="Dining room temp", type="tempF")
    hallTemp = Sensor("hallTemp", owfs, "28.FA78DB060000", group=["Hvac", "Temperature"], label="Hall temp", type="tempF")
    atticTemp = Sensor("atticTemp", owfs, "28.CC02DC060000", group=["Hvac", "Temperature"], label="Attic temp", type="tempF")
    livingRoomTemp = Sensor("livingRoomTemp", owfs, "28.11B2DB060000", group=["Hvac", "Temperature"], label="Living room temp", type="tempF")
    familyRoomTemp = Sensor("familyRoomTemp", owfs, "28.7202DC060000", group=["Hvac", "Temperature"], label="Family room temp", type="tempF")
    
    # HVAC equipment controls
    northHeat = Control("northHeat", gpio1, 4, group="Hvac", label="North heat")
    southHeat = Control("southHeat", gpio1, 0, group="Hvac", label="South heat")
    northCool = Control("northCool", gpio1, 5, group="Hvac", label="North cool")
    southCool = Control("southCool", gpio1, 1, group="Hvac", label="South cool")
    northFan  = Control("northFan",  gpio1, 6, group="Hvac", label="North fan")
    southFan  = Control("southFan",  gpio1, 2, group="Hvac", label="South fan")

    # Temp controls
    northHeatControl = TempControl("northHeatControl", nullInterface, 
                                    northHeat, masterBedroomTemp, northHeatTempTarget, unitType=unitTypeHeater, 
                                    group="Hvac", label="North heat control", type="tempControl")
    northCoolControl = TempControl("northCoolControl", nullInterface, 
                                    northCool, masterBedroomTemp, northCoolTempTarget, unitType=unitTypeAc, 
                                    group="Hvac", label="North cool control", type="tempControl")
    southHeatControl = TempControl("southHeatControl", nullInterface, 
                                    southHeat, diningRoomTemp, southHeatTempTarget, unitType=unitTypeHeater, 
                                    group="Hvac", label="South heat control", type="tempControl")
    southCoolControl = TempControl("southCoolControl", nullInterface, 
                                    southCool, diningRoomTemp, southCoolTempTarget, unitType=unitTypeAc, 
                                    group="Hvac", label="South cool control", type="tempControl")

    # Thermostats
    northThermostat = ThermostatControl("northThermostat", nullInterface, 
                                    northHeatControl, northCoolControl, northFan, masterBedroomDoor, northThermostatMode,
                                    group="Hvac", label="North thermostat", type="thermostat")
    northThermostatUnitSensor = ThermostatUnitSensor("northThermostatUnitSensor", northThermostat,
                                    group="Hvac", label="North thermostat unit", type="thermostat")
    southThermostat = ThermostatControl("southThermostat", nullInterface, 
                                    southHeatControl, southCoolControl, southFan, familyRoomDoor, southThermostatMode,
                                    group="Hvac", label="South thermostat", type="thermostat")
    southThermostatUnitSensor = ThermostatUnitSensor("southThermostatUnitSensor", southThermostat,
                                    group="Hvac", label="South thermostat unit", type="thermostat")

    # Tasks
    northHeatTempUpMorning = Task("northHeatTempUpMorning", SchedTime(hour=[6], minute=[0]), northHeatTempTarget, 69)
    southHeatTempUpMorning = Task("southHeatTempUpMorning", SchedTime(hour=[6], minute=[0]), southHeatTempTarget, 70)
    northHeatTempDownMorning = Task("northHeatTempDownMorning", SchedTime(hour=[8], minute=[0]), northHeatTempTarget, 66)
    southHeatTempDownMorning = Task("southHeatTempDownMorning", SchedTime(hour=[8], minute=[0]), southHeatTempTarget, 67)
    northHeatTempDownEvening = Task("northHeatTempDownEvening", SchedTime(hour=[21], minute=[0]), northHeatTempTarget, 66)
    southHeatTempDownEvening = Task("southHeatTempDownEvening", SchedTime(hour=[21], minute=[0]), southHeatTempTarget, 67)
    
    # Schedule
    schedule = Schedule("schedule", tasks=[northHeatTempUpMorning, northHeatTempDownMorning, northHeatTempDownEvening,
                                           southHeatTempUpMorning, southHeatTempDownMorning, southHeatTempDownEvening])

    # Resources
    resources = Collection("resources", resources=[frontDoor, familyRoomDoor, masterBedroomDoor, houseDoors,
                                                   atticTemp, hallTemp, masterBedroomTemp, livingRoomTemp, familyRoomTemp, diningRoomTemp,
                                                   northHeat, northCool, northFan, northHeatTempTarget, northCoolTempTarget, 
                                                   northHeatControl, northCoolControl, northThermostat, northThermostatUnitSensor,
                                                   southHeat, southCool, southFan, southHeatTempTarget, southCoolTempTarget, 
                                                   southHeatControl, southCoolControl, southThermostat, southThermostatUnitSensor, 
                                                   northHeatTempUpMorning, northHeatTempDownMorning, northHeatTempDownEvening,
                                                   southHeatTempUpMorning, southHeatTempDownMorning, southHeatTempDownEvening
                                                   ])
    restServer = RestServer(resources, event=stateChangeEvent, label="Hvac")

    # Start interfaces
    configData.start()
    if not northHeatTempTarget.getState():
        northHeatTempTarget.setState(northHeatTempTargetDefault)
    if not northCoolTempTarget.getState():
        northCoolTempTarget.setState(northCoolTempTargetDefault)
    if not southHeatTempTarget.getState():
        southHeatTempTarget.setState(southHeatTempTargetDefault)
    if not southCoolTempTarget.getState():
        southCoolTempTarget.setState(southCoolTempTargetDefault)
    gpio0.start()
    gpio1.start()
    northThermostat.start()
    southThermostat.start()
    schedule.start()
    restServer.start()

