
doorbellState = 0
doorbellSound = "addamsdoorbell.wav"
doorbellNotifyMsg = "Doorbell "

import time
from ha import *
from ha.interfaces.mcp23017Interface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.owfsInterface import *
from ha.interfaces.tempInterface import *
from ha.interfaces.ledInterface import *
from ha.interfaces.fileInterface import *
from ha.rest.restServer import *
from ha.notification.notificationClient import *

doorbellEvent = threading.Event()
def doorbellHandler(doorbellControl):
    debug('debugDoorbell', "starting doorbellHandler using control", doorbellControl.name)
    while True:
        doorbellEvent.wait()
        doorbellEvent.clear()
        doorbellControl.setState(1)
        debug('debugDoorbell', "sending notification")
        notify("alertDoorbell", doorbellNotifyMsg)
        debug('debugDoorbell', "playing", soundDir+doorbellSound)
        os.system("aplay "+soundDir+doorbellSound)

def doorbellInterrupt(sensor, state):
    global doorbellState
    debug('debugDoorbell', "state:", state, "doorbellState:", doorbellState)
    if (state == 1) and (state != doorbellState):
        doorbellEvent.set()
    doorbellState = state

class GarageDoorControl(Control):
    def __init__(self, name, interface, doorControl, doorClosedSensor, doorOpenSensor=None, addr=None,
            group="", type="control", location=None, label="", interrupt=None, event=None):
        Control.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Control"
        self.doorControl = doorControl
        self.doorClosedSensor = doorClosedSensor
        self.doorOpenSensor = doorOpenSensor

    def getState(self):
        return self.doorClosedSensor.getState()

    def setState(self, value):
        if value != self.doorClosedSensor.getState():
            return self.doorControl.setState(1)

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1)
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    gpio0 = MCP23017Interface("gpio0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = MCP23017Interface("gpio1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(MCP23017Interface.IPOL, 0x08)])
    led = LedInterface("led", gpio0)
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"garage.state", event=stateChangeEvent)

    # Temperature
    garageTemp = Sensor("garageTemp", owfs, "28.556E5F070000", group="Temperature", label="Garage temp", type="tempF", event=stateChangeEvent)

    # Water
    recircPump = Control("recircPump", gpio0, 0, type="hotwater", group="Water", label="Hot water")

    # Lights
    sculptureLights = Control("sculptureLights", led, 1, type="led", group="Lights", label="Sculpture")

    # Doors
    garageDoorControl = MomentaryControl("garageDoorControl", gpio0, 2, duration=.5, group="Doors", label="Garage door control")
    garageDoorClosed = Sensor("garageDoorClosed", gpio1, 0, type="door", group="Doors", label="Garage", event=stateChangeEvent)
    garageDoor = GarageDoorControl("garageDoor", None, garageDoorControl, garageDoorClosed, type="door", group="Doors", label="Garage door", event=stateChangeEvent)
    garageBackDoor = Sensor("garageBackDoor", gpio1, 1, type="door", group="Doors", label="Garage back", event=stateChangeEvent)
    garageHouseDoor = Sensor("garageHouseDoor", gpio1, 2, type="door", group="Doors", label="Garage house", event=stateChangeEvent)
    garageDoors = SensorGroup("garageDoors", [garageDoor, garageBackDoor, garageHouseDoor], type="door", group="Doors", label="Garage doors")
    doorbellButton = Sensor("doorbellButton", gpio1, 3, interrupt=doorbellInterrupt)
    doorbell = MomentaryControl("doorbell", None, duration=10, type="sound", group="Doors", label="Doorbell", event=stateChangeEvent)

    # Tasks
    hotWaterRecirc = Task("hotWaterRecirc", SchedTime(hour=[5], minute=[0]), recircPump, 1, endTime=SchedTime(hour=[23], minute=[0]), group="Water")

    # Schedule
    schedule = Schedule("schedule", tasks=[hotWaterRecirc])

    # Resources
    resources = Collection("resources", resources=[recircPump, sculptureLights, doorbell,
                                                   garageDoorControl, garageDoorClosed, garageDoor,
                                                   garageBackDoor, garageHouseDoor, garageDoors,
                                                   doorbellButton,
                                                   hotWaterRecirc, garageTemp,
                                                   ])
    restServer = RestServer("garage", resources, event=stateChangeEvent, label="Garage")

    # Start interfaces
    doorbellThread = threading.Thread(target=doorbellHandler, args=(doorbell,))
    doorbellThread.start()
    gpio0.start()
    gpio1.start()
    fileInterface.start()
    schedule.start()
    restServer.start()
