import threading

from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.owfsInterface import *
from ha.tempInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpioInterface = GPIOInterface("GPIO", i2c1)
    
    # Temperature
    resources.addRes(HASensor("temp1", owfs, "28.175CDC060000", group="Temperature", label="Master bedroom", type="tempF"))
    resources.addRes(HASensor("temp2", owfs, "28.7202DC060000", group="Temperature", label="Kitchen", type="tempF"))
    resources.addRes(HASensor("temp3", owfs, "28.FA78DB060000", group="Temperature", label="Living room", type="tempF"))
    resources.addRes(HASensor("temp4", owfs, "28.CC02DC060000", group="Temperature", label="Attic", type="tempF"))
    resources.addRes(HASensor("temp5", owfs, "28.E4F6DB060000", group="Temperature", label="Office", type="tempF"))
    
    # HVAC
    resources.addRes(HAControl("northHeat", gpioInterface, 7, group="Hvac", label="North heater")) # yellow

    # Start interfaces
    gpioInterface.start()
    restServer = RestServer(resources, port=7380, event=stateChangeEvent, label="Temperature")
    restServer.start()

