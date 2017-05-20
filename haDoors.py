from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.rest.restServer import *
from ha.interfaces.restInterface import *

if __name__ == "__main__":
    global stateChangeEvent

    # Resources
    resources = Collection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x21, bank=0, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x21, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL, 0x00)])

    # Doors
#    resources.addRes(Sensor("door00", gpio0, 0, type="door", group="Doors", label="door00"))
#    resources.addRes(Sensor("door01", gpio0, 1, type="door", group="Doors", label="door01"))
#    resources.addRes(Sensor("door02", gpio0, 2, type="door", group="Doors", label="door02"))
#    resources.addRes(Sensor("door03", gpio0, 3, type="door", group="Doors", label="door03"))
#    resources.addRes(Sensor("door04", gpio0, 4, type="door", group="Doors", label="door04"))
#    resources.addRes(Sensor("door05", gpio0, 5, type="door", group="Doors", label="door05"))
#    resources.addRes(Sensor("door06", gpio0, 6, type="door", group="Doors", label="door06"))
#    resources.addRes(Sensor("door07", gpio0, 7, type="door", group="Doors", label="door07"))
#    resources.addRes(Sensor("officeWindow", gpio1, 0, type="door", group="Doors", label="Office window"))
#    resources.addRes(Sensor("door11", gpio1, 1, type="door", group="Doors", label="door11"))
#    resources.addRes(Sensor("door12", gpio1, 2, type="door", group="Doors", label="door12"))
#    resources.addRes(Sensor("door13", gpio1, 3, type="door", group="Doors", label="door13"))
#    resources.addRes(Sensor("door14", gpio1, 4, type="door", group="Doors", label="door14"))
    resources.addRes(Sensor("frontDoor", gpio1, 5, type="door", group="Doors", label="Front"))
    resources.addRes(Sensor("familyRoomDoor", gpio1, 6, type="door", group="Doors", label="Family room"))
    resources.addRes(Sensor("masterBedroomDoor", gpio1, 7, type="door", group="Doors", label="Master bedroom"))
    resources.addRes(SensorGroup("houseDoors", ["frontDoor", "familyRoomDoor", "masterBedroomDoor"], resources=resources, type="door", group="Doors", label="House doors"))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    restServer = RestServer(resources, port=7379, event=stateChangeEvent, label="Doors")
    restServer.start()

