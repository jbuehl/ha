northHeatTempTargetDefault = 65
southHeatTempTargetDefault = 66

import threading
from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.owfsInterface import *
from ha.fileInterface import *
from ha.tempInterface import *
from ha.heaterControl import *
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
    gpioInterface = GPIOInterface("GPIO", i2c1)
    
    # persistent config data
    northHeatTempTarget = HAControl("northHeatTempTarget", configData, "northHeatTempTarget", group="Hvac", label="North heat set", type="tempFControl")
    southHeatTempTarget = HAControl("southHeatTempTarget", configData, "southHeatTempTarget", group="Hvac", label="South heat set", type="tempFControl")
   
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
    northHeat = HAControl("northHeat", gpioInterface, 4, group="Hvac", label="North heat")
    southHeat = HAControl("southHeat", gpioInterface, 0, group="Hvac", label="South heat")
    northCool = HAControl("northCool", gpioInterface, 5, group="Hvac", label="North cool")
    southCool = HAControl("southCool", gpioInterface, 1, group="Hvac", label="South cool")
    northFan  = HAControl("northFan",  gpioInterface, 6, group="Hvac", label="North fan")
    southFan  = HAControl("southFan",  gpioInterface, 2, group="Hvac", label="South fan")

    # Thermostats
    northThermostat = HeaterControl("northThermostat", nullInterface, northHeat, masterBedroomTemp, northHeatTempTarget, group="Hvac", label="North thermostat", type="heater")
    southThermostat = HeaterControl("southThermostat", nullInterface, southHeat, kitchenTemp, southHeatTempTarget, group="Hvac", label="South thermostat", type="heater")
    resources.addRes(northHeat)
    resources.addRes(northCool)
    resources.addRes(northFan)
    resources.addRes(northHeatTempTarget)
    resources.addRes(northThermostat)
    resources.addRes(southHeat)
    resources.addRes(southCool)
    resources.addRes(southFan)
    resources.addRes(southHeatTempTarget)
    resources.addRes(southThermostat)

    # Tasks
    resources.addRes(HATask("northHeatNight", HASchedTime(hour=[21], minute=[00]), northHeatTempTarget, 65))
    resources.addRes(HATask("southHeatNight", HASchedTime(hour=[21], minute=[00]), southHeatTempTarget, 65))
    resources.addRes(HATask("southHeatMorning", HASchedTime(hour=[6], minute=[00]), southHeatTempTarget, 70))
    
    # Schedule
    schedule = HASchedule("schedule")
    schedule.addTask(resources["northHeatNight"])
    schedule.addTask(resources["southHeatNight"])
    schedule.addTask(resources["southHeatMorning"])
    schedule.start()

    # Start interfaces
    configData.start()
    if not northHeatTempTarget.getState():
        northHeatTempTarget.setState(northHeatTempTargetDefault)
    if not southHeatTempTarget.getState():
        southHeatTempTarget.setState(southHeatTempTargetDefault)
    # temporary
    northThermostat.setState(1)
    southThermostat.setState(1)
    northHeat.setState(1)
    southHeat.setState(1)

    gpioInterface.start()
    restServer = RestServer(resources, port=7380, event=stateChangeEvent, label="Hvac")
    restServer.start()

