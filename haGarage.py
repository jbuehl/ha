from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.restServer import *
from ha.restInterface import *

if __name__ == "__main__":
    global stateChangeEvent

    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])
    tc74 = TC74Interface("TC74", i2c1)
    temp = TempInterface("Temp", tc74, sample=10)
    
    # Lights
#    resources.addRes(HAControl("garageBackDoorLight", gpio0, 1, type="light", group="Lights", label="Garage back door light"))

    # Doors
    resources.addRes(HASensor("garageBackDoor", gpio1, 1, type="door", group="Doors", label="Garage Back"))
    resources.addRes(HASensor("garageDoor", gpio1, 2, type="door", group="Doors", label="Garage Door"))
    resources.addRes(HASensor("garageHouseDoor", gpio1, 3, type="door", group="Doors", label="Garage House"))
    resources.addRes(SensorGroup("garageDoors", ["garageDoor", "garageBackDoor", "garageHouseDoor"], resources=resources, type="door", group="Doors", label="Garage doors"))

    # Temperature
    resources.addRes(HASensor("garageTemp", temp, 0x4d, group="Temperature", label="Garage temp", type="tempF"))
    
    # Start interfaces
    gpio0.start()
    gpio1.start()
    temp.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Garage")
    restServer.start()

