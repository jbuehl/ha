northHeatTemp = 67

import threading
from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.owfsInterface import *
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
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpioInterface = GPIOInterface("GPIO", i2c1)
    
    # Temperature
    masterBedroomTemp = HASensor("masterBedroomTemp", owfs, "28.175CDC060000", group="Temperature", label="Master bedroom temp", type="tempF")
    kitchenTemp = HASensor("kitchenTemp", owfs, "28.7202DC060000", group="Temperature", label="Kitchen temp", type="tempF")
    livingRoomTempHASensor("livingRoomTemp", owfs, "28.FA78DB060000", group="Temperature", label="Living room temp", type="tempF")
    atticTemp = HASensor("atticTemp", owfs, "28.CC02DC060000", group="Temperature", label="Attic temp", type="tempF")
    officeTemp = HASensor("officeTemp", owfs, "28.E4F6DB060000", group="Temperature", label="Office temp", type="tempF")
    resources.addRes(masterBedroomTemp)
    resources.addRes(kitchenTemp)
    resources.addRes(livingRoomTemp)
    resources.addRes(atticTemp)
    resources.addRes(officeTemp)
    
    # HVAC
    northHeater = HAControl("northHeater", gpioInterface, 7, group="Hvac", label="North heater")
    northThermostat = HeaterControl("northThermostat", nullInterface, northHeater, masterBedroomTemp, group="Hvac", label="North thermostat", type="heater")
    northThermostat.setTarget(northHeatTemp)
    resources.addRes(northHeater)
    resources.addRes(northThermostat)
    
    # Start interfaces
    gpioInterface.start()
    restServer = RestServer(resources, port=7380, event=stateChangeEvent, label="Hvac")
    restServer.start()

