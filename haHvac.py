northHeatTempTargetDefault = 65
northCoolTempTargetDefault = 75
southHeatTempTargetDefault = 65
southCoolTempTargetDefault = 75

import threading
from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.owfsInterface import *
from ha.fileInterface import *
from ha.tempInterface import *
from ha.tempControl import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    nullInterface = HAInterface("Null", HAInterface("None"))
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    configData = FileInterface("config", fileName=rootDir+"hvac.conf", event=stateChangeEvent)
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio00 = GPIOInterface("GPIO00", i2c1, addr=0x20, bank=0)
    gpio10 = GPIOInterface("GPIO10", i2c1, addr=0x21, bank=0, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])
    gpio11 = GPIOInterface("GPIO11", i2c1, addr=0x21, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])

    # Doors
#    resources.addRes(HASensor("door00", gpio10, 0, type="door", group="Doors", label="door00"))
#    resources.addRes(HASensor("door01", gpio10, 1, type="door", group="Doors", label="door01"))
#    resources.addRes(HASensor("door02", gpio10, 2, type="door", group="Doors", label="door02"))
#    resources.addRes(HASensor("door03", gpio10, 3, type="door", group="Doors", label="door03"))
#    resources.addRes(HASensor("door04", gpio10, 4, type="door", group="Doors", label="door04"))
#    resources.addRes(HASensor("door05", gpio10, 5, type="door", group="Doors", label="door05"))
#    resources.addRes(HASensor("door06", gpio10, 6, type="door", group="Doors", label="door06"))
#    resources.addRes(HASensor("door07", gpio10, 7, type="door", group="Doors", label="door07"))
#    resources.addRes(HASensor("officeWindow", gpio11, 0, type="door", group="Doors", label="Office window"))
#    resources.addRes(HASensor("door11", gpio11, 1, type="door", group="Doors", label="door11"))
#    resources.addRes(HASensor("door12", gpio11, 2, type="door", group="Doors", label="door12"))
#    resources.addRes(HASensor("door13", gpio11, 3, type="door", group="Doors", label="door13"))
#    resources.addRes(HASensor("door14", gpio11, 4, type="door", group="Doors", label="door14"))
    resources.addRes(HASensor("frontDoor", gpio11, 5, type="door", group="Doors", label="Front"))
    resources.addRes(HASensor("familyRoomDoor", gpio11, 6, type="door", group="Doors", label="Family room"))
    resources.addRes(HASensor("masterBedroomDoor", gpio11, 7, type="door", group="Doors", label="Master bedroom"))
    resources.addRes(SensorGroup("houseDoors", ["frontDoor", "familyRoomDoor", "masterBedroomDoor"], resources=resources, type="door", group="Doors", label="House doors"))

    # persistent config data
    northHeatTempTarget = HAControl("northHeatTempTarget", configData, "northHeatTempTarget", group="Hvac", label="North heat set", type="tempFControl")
    northCoolTempTarget = HAControl("northCoolTempTarget", configData, "northCoolTempTarget", group="Hvac", label="North cool set", type="tempFControl")
    southHeatTempTarget = HAControl("southHeatTempTarget", configData, "southHeatTempTarget", group="Hvac", label="South heat set", type="tempFControl")
    southCoolTempTarget = HAControl("southCoolTempTarget", configData, "southCoolTempTarget", group="Hvac", label="South cool set", type="tempFControl")
   
    # Temperature sensors
    masterBedroomTemp = HASensor("masterBedroomTemp", owfs, "28.175CDC060000", group="Temperature", label="Master bedroom temp", type="tempF")
    kitchenTemp = HASensor("kitchenTemp", owfs, "28.E4F6DB060000", group="Temperature", label="Kitchen temp", type="tempF")
    hallTemp = HASensor("hallTemp", owfs, "28.FA78DB060000", group="Temperature", label="Hall temp", type="tempF")
    atticTemp = HASensor("atticTemp", owfs, "28.CC02DC060000", group="Temperature", label="Attic temp", type="tempF")
#    officeTemp = HASensor("officeTemp", owfs, "", group="Temperature", label="Office temp", type="tempF")
    livingRoomTemp = HASensor("livingRoomTemp", owfs, "28.B9CA5F070000", group="Temperature", label="Living room temp", type="tempF")
    familyRoomTemp = HASensor("familyRoomTemp", owfs, "28.7202DC060000", group="Temperature", label="Family room temp", type="tempF")
    resources.addRes(atticTemp)
    resources.addRes(hallTemp)
#    resources.addRes(officeTemp)
    resources.addRes(masterBedroomTemp)
    resources.addRes(livingRoomTemp)
    resources.addRes(familyRoomTemp)
    resources.addRes(kitchenTemp)
    
    # HVAC equipment
    northHeat = HAControl("northHeat", gpio00, 4, group="Hvac", label="North heat")
    southHeat = HAControl("southHeat", gpio00, 0, group="Hvac", label="South heat")
    northCool = HAControl("northCool", gpio00, 5, group="Hvac", label="North cool")
    southCool = HAControl("southCool", gpio00, 1, group="Hvac", label="South cool")
    northFan  = HAControl("northFan",  gpio00, 6, group="Hvac", label="North fan")
    southFan  = HAControl("southFan",  gpio00, 2, group="Hvac", label="South fan")

    # Temp controls
    northHeatControl = TempControl("northHeatControl", nullInterface, northHeat, masterBedroomTemp, northHeatTempTarget, unitType=0, group="Hvac", label="North heat control", type="heater")
    northCoolControl = TempControl("northCoolControl", nullInterface, northCool, masterBedroomTemp, northCoolTempTarget, unitType=1, group="Hvac", label="North cool control", type="heater")
    southHeatControl = TempControl("southHeatControl", nullInterface, southHeat, kitchenTemp, southHeatTempTarget, unitType=0, group="Hvac", label="South heat control", type="heater")
    southCoolControl = TempControl("southCoolControl", nullInterface, southCool, kitchenTemp, southCoolTempTarget, unitType=1, group="Hvac", label="South cool control", type="heater")
    
    resources.addRes(northHeat)
    resources.addRes(northCool)
    resources.addRes(northFan)
    resources.addRes(northHeatTempTarget)
    resources.addRes(northCoolTempTarget)
    resources.addRes(northHeatControl)
    resources.addRes(northCoolControl)
    resources.addRes(southHeat)
    resources.addRes(southCool)
    resources.addRes(southFan)
    resources.addRes(southHeatTempTarget)
    resources.addRes(southCoolTempTarget)
    resources.addRes(southHeatControl)
    resources.addRes(southCoolControl)

    # Tasks
#    resources.addRes(HATask("northHeatNight", HASchedTime(hour=[21], minute=[00]), northHeatTempTarget, 65))
#    resources.addRes(HATask("southHeatNight", HASchedTime(hour=[21], minute=[00]), southHeatTempTarget, 65))
#    resources.addRes(HATask("southHeatMorning", HASchedTime(hour=[6], minute=[00]), southHeatTempTarget, 70))
    
    # Schedule
#    schedule = HASchedule("schedule")
#    schedule.addTask(resources["northHeatNight"])
#    schedule.addTask(resources["southHeatNight"])
#    schedule.addTask(resources["southHeatMorning"])
#    schedule.start()

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
    # temporary
    northCoolControl.setState(1)
    southCoolControl.setState(1)
    northCool.setState(1)
    southCool.setState(1)

    gpio00.start()
    gpio10.start()
    gpio11.start()
    restServer = RestServer(resources, port=7378, event=stateChangeEvent, label="Hvac")
    restServer.start()

