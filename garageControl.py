from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.tc74Interface import *
from ha.interfaces.tempInterface import *
from ha.interfaces.ledInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("gpio0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = GPIOInterface("gpio1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL, 0x08)])
    led = LedInterface("led", gpio0)
    tc74 = TC74Interface("tc74", i2c1)
    temp = TempInterface("temp", tc74, sample=10)
    
    # Water
    recircPump = Control("recircPump", gpio0, 0, type="hotwater", group="Water", label="Hot water")

    # Lights
    sculptureLights = Control("sculptureLights", led, 7, type="led", group="Lights", label="Sculpture")

    # Doors
    garageDoor = Sensor("garageDoor", gpio1, 0, type="door", group="Doors", label="Garage Door")
    garageBackDoor = Sensor("garageBackDoor", gpio1, 1, type="door", group="Doors", label="Garage Back")
    garageHouseDoor = Sensor("garageHouseDoor", gpio1, 2, type="door", group="Doors", label="Garage House")
    garageDoors = SensorGroup("garageDoors", [garageDoor, garageBackDoor, garageHouseDoor], type="door", group="Doors", label="Garage doors")
    doorbellButton = Sensor("doorbellButton", gpio1, 3)

    # Temperature
    garageTemp = Sensor("garageTemp", temp, 0x4d, group="Temperature", label="Garage temp", type="tempF")
    
    # Tasks
    hotWaterRecircOn = Task("hotWaterRecircOn", SchedTime(hour=[05], minute=[0]), recircPump, 1)
    hotWaterRecircOff = Task("hotWaterRecircOff", SchedTime(hour=[23], minute=[0]), recircPump, 0)
    
    # Schedule
    schedule = Schedule("schedule", tasks=[hotWaterRecircOn, hotWaterRecircOff])

    # Resources
    resources = Collection("resources", resources=[recircPump, sculptureLights, garageDoor, garageBackDoor, garageHouseDoor, 
            garageDoors, doorbellButton, garageTemp, hotWaterRecircOn, hotWaterRecircOff])
    restServer = RestServer(resources, event=stateChangeEvent, label="Garage")

    # Start interfaces
    gpio0.start()
    gpio1.start()
    temp.start()
    schedule.start()
    restServer.start()

