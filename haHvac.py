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
from ha.rest.restServer import *

if __name__ == "__main__":
    # Resources
    resources = Collection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    nullInterface = Interface("NullInterface", event=stateChangeEvent)
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"hvac.conf", event=stateChangeEvent)
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio10 = GPIOInterface("GPIO10", i2c1, addr=0x20, bank=0, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])
    gpio11 = GPIOInterface("GPIO11", i2c1, addr=0x20, bank=1, inOut=0x00)

    # Doors
#    resources.addRes(Sensor("door00", gpio10, 0, type="door", group="Doors", label="door00"))
#    resources.addRes(Sensor("door01", gpio10, 1, type="door", group="Doors", label="door01"))
#    resources.addRes(Sensor("door02", gpio10, 2, type="door", group="Doors", label="door02"))
#    resources.addRes(Sensor("door03", gpio10, 3, type="door", group="Doors", label="door03"))
#    resources.addRes(Sensor("door04", gpio10, 4, type="door", group="Doors", label="door04"))
#    resources.addRes(Sensor("door05", gpio10, 5, type="door", group="Doors", label="door05"))
#    resources.addRes(Sensor("door06", gpio10, 6, type="door", group="Doors", label="door06"))
#    resources.addRes(Sensor("door07", gpio10, 7, type="door", group="Doors", label="door07"))
#    resources.addRes(Sensor("officeWindow", gpio11, 0, type="door", group="Doors", label="Office window"))
#    resources.addRes(Sensor("door11", gpio11, 1, type="door", group="Doors", label="door11"))
#    resources.addRes(Sensor("door12", gpio11, 2, type="door", group="Doors", label="door12"))
#    resources.addRes(Sensor("door13", gpio11, 3, type="door", group="Doors", label="door13"))
#    resources.addRes(Sensor("door14", gpio11, 4, type="door", group="Doors", label="door14"))
    frontDoor = Sensor("frontDoor", gpio10, 5, type="door", group="Doors", label="Front")
    familyRoomDoor = Sensor("familyRoomDoor", gpio10, 6, type="door", group="Doors", label="Family room")
    masterBedroomDoor = Sensor("masterBedroomDoor", gpio10, 7, type="door", group="Doors", label="Master bedroom")
    houseDoors = SensorGroup("houseDoors", ["frontDoor", "familyRoomDoor", "masterBedroomDoor"], resources=resources, type="door", group="Doors", label="House doors")
    resources.addRes(frontDoor)
    resources.addRes(familyRoomDoor)
    resources.addRes(masterBedroomDoor)
    resources.addRes(houseDoors)

    # persistent config data
    northHeatTempTarget = Control("northHeatTempTarget", configData, "northHeatTempTarget", group="Hvac", label="North heat set", type="tempFControl")
    northCoolTempTarget = Control("northCoolTempTarget", configData, "northCoolTempTarget", group="Hvac", label="North cool set", type="tempFControl")
    southHeatTempTarget = Control("southHeatTempTarget", configData, "southHeatTempTarget", group="Hvac", label="South heat set", type="tempFControl")
    southCoolTempTarget = Control("southCoolTempTarget", configData, "southCoolTempTarget", group="Hvac", label="South cool set", type="tempFControl")
   
    # Temperature sensors
    masterBedroomTemp = Sensor("masterBedroomTemp", owfs, "28.175CDC060000", group="Temperature", label="Master bedroom temp", type="tempF")
    kitchenTemp = Sensor("diningRoomTemp", owfs, "28.E4F6DB060000", group="Temperature", label="Dining room temp", type="tempF")
    hallTemp = Sensor("hallTemp", owfs, "28.FA78DB060000", group="Temperature", label="Hall temp", type="tempF")
    atticTemp = Sensor("atticTemp", owfs, "28.CC02DC060000", group="Temperature", label="Attic temp", type="tempF")
#    officeTemp = Sensor("officeTemp", owfs, "", group="Temperature", label="Office temp", type="tempF")
    livingRoomTemp = Sensor("livingRoomTemp", owfs, "28.B9CA5F070000", group="Temperature", label="Living room temp", type="tempF")
    familyRoomTemp = Sensor("familyRoomTemp", owfs, "28.7202DC060000", group="Temperature", label="Family room temp", type="tempF")
    resources.addRes(atticTemp)
    resources.addRes(hallTemp)
#    resources.addRes(officeTemp)
    resources.addRes(masterBedroomTemp)
    resources.addRes(livingRoomTemp)
    resources.addRes(familyRoomTemp)
    resources.addRes(kitchenTemp)
    
    # HVAC equipment
    northHeat = Control("northHeat", gpio11, 4, group="Hvac", label="North heat")
    southHeat = Control("southHeat", gpio11, 0, group="Hvac", label="South heat")
    northCool = Control("northCool", gpio11, 5, group="Hvac", label="North cool")
    southCool = Control("southCool", gpio11, 1, group="Hvac", label="South cool")
    northFan  = Control("northFan",  gpio11, 6, group="Hvac", label="North fan")
    southFan  = Control("southFan",  gpio11, 2, group="Hvac", label="South fan")

    # Temp controls
    northHeatControl = TempControl("northHeatControl", nullInterface, 
                                    northHeat, masterBedroomTemp, northHeatTempTarget, masterBedroomDoor, unitType=0, 
                                    group="Hvac", label="North heat control", type="heater")
    northCoolControl = TempControl("northCoolControl", nullInterface, 
                                    northCool, masterBedroomTemp, northCoolTempTarget, masterBedroomDoor, unitType=1, 
                                    group="Hvac", label="North cool control", type="heater")
    southHeatControl = TempControl("southHeatControl", nullInterface, 
                                    southHeat, familyRoomTemp, southHeatTempTarget, familyRoomDoor, unitType=0, 
                                    group="Hvac", label="South heat control", type="heater")
    southCoolControl = TempControl("southCoolControl", nullInterface, 
                                    southCool, familyRoomTemp, southCoolTempTarget, familyRoomDoor, unitType=1, 
                                    group="Hvac", label="South cool control", type="heater")
    
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
    resources.addRes(Task("northHeatTempUpMorning", SchedTime(hour=[6], minute=[0]), "northHeatTempTarget", 69, resources=resources))
    resources.addRes(Task("southHeatTempUpMorning", SchedTime(hour=[6], minute=[0]), "southHeatTempTarget", 70, resources=resources))
    resources.addRes(Task("northHeatTempDownMorning", SchedTime(hour=[8], minute=[0]), "northHeatTempTarget", 66, resources=resources))
    resources.addRes(Task("southHeatTempDownMorning", SchedTime(hour=[8], minute=[0]), "southHeatTempTarget", 67, resources=resources))
    resources.addRes(Task("northHeatTempDownEvening", SchedTime(hour=[21], minute=[0]), "northHeatTempTarget", 66, resources=resources))
    resources.addRes(Task("southHeatTempDownEvening", SchedTime(hour=[21], minute=[0]), "southHeatTempTarget", 67, resources=resources))
    
    # Schedule
    schedule = Schedule("schedule")
    schedule.addTask(resources["northHeatTempUpMorning"])
    schedule.addTask(resources["southHeatTempUpMorning"])
    schedule.addTask(resources["northHeatTempDownMorning"])
    schedule.addTask(resources["southHeatTempDownMorning"])
    schedule.addTask(resources["northHeatTempDownEvening"])
    schedule.addTask(resources["southHeatTempDownEvening"])
    schedule.start()

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
    northHeatControl.setState(1)
    southHeatControl.setState(1)
    northCoolControl.setState(1)
    southCoolControl.setState(1)
#    northCool.setState(1)
#    southCool.setState(1)

#    gpio00.start()
    gpio10.start()
    gpio11.start()
    restServer = RestServer(resources, port=7378, event=stateChangeEvent, label="Hvac")
    restServer.start()

