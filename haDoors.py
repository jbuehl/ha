from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.restServer import *
from ha.restInterface import *

if __name__ == "__main__":
    global stateChangeEvent

    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x21, bank=0, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x21, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])

    # Doors
#    resources.addRes(HASensor("door00", gpio0, 0, type="door", group="Doors", label="door00"))
#    resources.addRes(HASensor("door01", gpio0, 1, type="door", group="Doors", label="door01"))
#    resources.addRes(HASensor("door02", gpio0, 2, type="door", group="Doors", label="door02"))
#    resources.addRes(HASensor("door03", gpio0, 3, type="door", group="Doors", label="door03"))
#    resources.addRes(HASensor("door04", gpio0, 4, type="door", group="Doors", label="door04"))
#    resources.addRes(HASensor("door05", gpio0, 5, type="door", group="Doors", label="door05"))
#    resources.addRes(HASensor("door06", gpio0, 6, type="door", group="Doors", label="door06"))
#    resources.addRes(HASensor("door07", gpio0, 7, type="door", group="Doors", label="door07"))
#    resources.addRes(HASensor("officeWindow", gpio1, 0, type="door", group="Doors", label="Office window"))
#    resources.addRes(HASensor("door11", gpio1, 1, type="door", group="Doors", label="door11"))
#    resources.addRes(HASensor("door12", gpio1, 2, type="door", group="Doors", label="door12"))
#    resources.addRes(HASensor("door13", gpio1, 3, type="door", group="Doors", label="door13"))
#    resources.addRes(HASensor("door14", gpio1, 4, type="door", group="Doors", label="door14"))
    resources.addRes(HASensor("frontDoor", gpio1, 5, type="door", group="Doors", label="Front"))
    resources.addRes(HASensor("familyRoomDoor", gpio1, 6, type="door", group="Doors", label="Family room"))
    resources.addRes(HASensor("masterBedroomDoor", gpio1, 7, type="door", group="Doors", label="Master bedroom"))
    resources.addRes(SensorGroup("houseDoors", ["frontDoor", "familyRoomDoor", "masterBedroomDoor"], resources=resources, type="door", group="Doors", label="House doors"))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    restServer = RestServer(resources, port=7379, event=stateChangeEvent, label="Doors")
    restServer.start()

