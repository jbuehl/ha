from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.restServer import *
from ha.restInterface import *

def doorInterrupt(sensor, state):
    log(sensor.name, "state:", state)
    stateChangeEvent.set()
    
if __name__ == "__main__":
    global stateChangeEvent

    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x20, bank=0, inOut=0x00, interruptPin=17)
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x20, bank=1, inOut=0xff, interruptPin=18, config=[(GPIOInterface.IPOL+1, 0xf9)])
    tc74 = TC74Interface("TC74", i2c1)
    temp = TempInterface("Temp", tc74, sample=10)
    
    # Lights
#    resources.addRes(HAControl("garageBackDoorLight", gpio0, 1, type="light", group="Lights", label="Garage back door light"))

    # Doors
    resources.addRes(HASensor("garageBackDoor", gpio1, 1, type="door", group="Doors", label="Garage Back", interrupt=doorInterrupt))
    resources.addRes(HASensor("garageDoor", gpio1, 2, type="door", group="Doors", label="Garage Door", interrupt=doorInterrupt))

    # Temperature
    resources.addRes(HASensor("garageTemp", temp, 0x4d, group="Temperature", label="Garage temp", type="tempF"))
    
    # Start interfaces
    gpio0.start()
    gpio1.start()
    temp.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Garage")
    restServer.start()

