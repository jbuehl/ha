from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
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
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x21, bank=0, inOut=0xff, interruptPin=17, config=[(GPIOInterface.IPOL+1, 0x00)])
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x21, bank=1, inOut=0xff, interruptPin=18, config=[(GPIOInterface.IPOL+1, 0x00)])

    # Doors
#    resources.addRes(HASensor("door00", gpio0, 0, type="door", group="Doors", label="door00", interrupt=doorInterrupt))
#    resources.addRes(HASensor("door01", gpio0, 1, type="door", group="Doors", label="door01", interrupt=doorInterrupt))
#    resources.addRes(HASensor("door02", gpio0, 2, type="door", group="Doors", label="door02", interrupt=doorInterrupt))
#    resources.addRes(HASensor("door03", gpio0, 3, type="door", group="Doors", label="door03", interrupt=doorInterrupt))
#    resources.addRes(HASensor("door04", gpio0, 4, type="door", group="Doors", label="door04", interrupt=doorInterrupt))
#    resources.addRes(HASensor("door05", gpio0, 5, type="door", group="Doors", label="door05", interrupt=doorInterrupt))
#    resources.addRes(HASensor("door06", gpio0, 6, type="door", group="Doors", label="door06", interrupt=doorInterrupt))
#    resources.addRes(HASensor("door07", gpio0, 7, type="door", group="Doors", label="door07", interrupt=doorInterrupt))
    resources.addRes(HASensor("door10", gpio1, 0, type="door", group="Doors", label="door10", interrupt=doorInterrupt))
    resources.addRes(HASensor("door11", gpio1, 1, type="door", group="Doors", label="door11", interrupt=doorInterrupt))
    resources.addRes(HASensor("door12", gpio1, 2, type="door", group="Doors", label="door12", interrupt=doorInterrupt))
    resources.addRes(HASensor("door13", gpio1, 3, type="door", group="Doors", label="door13", interrupt=doorInterrupt))
    resources.addRes(HASensor("door14", gpio1, 4, type="door", group="Doors", label="door14", interrupt=doorInterrupt))
    resources.addRes(HASensor("frontDoor", gpio1, 5, type="door", group="Doors", label="Front", interrupt=doorInterrupt))
    resources.addRes(HASensor("familyRoomDoor", gpio1, 6, type="door", group="Doors", label="Family room", interrupt=doorInterrupt))
    resources.addRes(HASensor("masterBedroomDoor", gpio1, 7, type="door", group="Doors", label="Master bedroom", interrupt=doorInterrupt))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    restServer = RestServer(resources, port=7379, event=stateChangeEvent, label="Doors")
    restServer.start()

