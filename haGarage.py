doorbellNotifyMsg = "Ding dong!"
notifyFromNumber = ""
doorbellNotifyNumbers = []

from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.tc74Interface import *
from ha.interfaces.tempInterface import *
from ha.interfaces.ledInterface import *
from ha.restServer import *
from ha.interfaces.restInterface import *
from ha.notify import *

def dingDong(sensor, state):
    sensorState = sensor.getState()
    debug('debugDoorbell', sensor.name, sensorState)
    if sensorState == 1:
        smsNotify(doorbellNotifyNumbers, doorbellNotifyMsg)
        
if __name__ == "__main__":
    global stateChangeEvent

    # Resources
    resources = Collection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL, 0x08)])
    led = LedInterface("LED", gpio0)
    tc74 = TC74Interface("TC74", i2c1)
    temp = TempInterface("Temp", tc74, sample=10)
    
    # Water
    resources.addRes(Control("recircPump", gpio0, 0, type="hotwater", group="Water", label="Hot water"))

    # Lights
    resources.addRes(Control("sculptureLights", led, 7, type="led", group="Lights", label="Sculpture"))

    # Doors
    resources.addRes(Sensor("garageDoor", gpio1, 0, type="door", group="Doors", label="Garage Door"))
    resources.addRes(Sensor("garageBackDoor", gpio1, 1, type="door", group="Doors", label="Garage Back"))
    resources.addRes(Sensor("garageHouseDoor", gpio1, 2, type="door", group="Doors", label="Garage House"))
    resources.addRes(SensorGroup("garageDoors", ["garageDoor", "garageBackDoor", "garageHouseDoor"], resources=resources, type="door", group="Doors", label="Garage doors"))
    resources.addRes(Sensor("doorbellButton", gpio1, 3, interrupt=dingDong))

    # Temperature
    resources.addRes(Sensor("garageTemp", temp, 0x4d, group="Temperature", label="Garage temp", type="tempF"))
    
    # Tasks
    resources.addRes(Task("hotWaterRecircOn", SchedTime(hour=[05], minute=[0]), "recircPump", 1, resources=resources))
    resources.addRes(Task("hotWaterRecircOff", SchedTime(hour=[23], minute=[0]), "recircPump", 0, resources=resources))
    
    # Schedule
    schedule = Schedule("schedule")
    schedule.addTask(resources["hotWaterRecircOn"])
    schedule.addTask(resources["hotWaterRecircOff"])
    schedule.start()

    # Start interfaces
    gpio0.start()
    gpio1.start()
    temp.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Garage")
    restServer.start()

