windSpeedAddr = 4
windDirAddr = 5
rainGaugeAddr = 6

doorbellState = 0
doorbellSound = "doorbell.wav"
doorbellNotifyMsg = "Doorbell "

from ha import *
from ha.interfaces.mcp23017Interface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.ledInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.windInterface import *
from ha.interfaces.rainInterface import *
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
        # debug('debugDoorbell', "playing", soundDir+doorbellSound)
        # os.system("aplay "+soundDir+doorbellSound)

def doorbellInterrupt(sensor, state):
    global doorbellState
    debug('debugDoorbell', "state:", state, "doorbellState:", doorbellState)
    if (state == 1) and (state != doorbellState):
        doorbellEvent.set()
    doorbellState = state

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1)
    gpio0 = MCP23017Interface("gpio0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = MCP23017Interface("gpio1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL, 0x08)])
    led = LedInterface("led", gpio0)
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"garage.state", event=stateChangeEvent)

    # Water
    recircPump = Control("recircPump", gpio0, 0, type="hotwater", group="Water", label="Hot water")

    # Lights
    sculptureLights = Control("sculptureLights", led, 1, type="led", group="Lights", label="Sculpture")

    # Doors
    garageDoor = Sensor("garageDoor", gpio1, 0, type="door", group="Doors", label="Garage", event=stateChangeEvent)
    garageBackDoor = Sensor("garageBackDoor", gpio1, 1, type="door", group="Doors", label="Garage back", event=stateChangeEvent)
    garageHouseDoor = Sensor("garageHouseDoor", gpio1, 2, type="door", group="Doors", label="Garage house", event=stateChangeEvent)
    garageDoors = SensorGroup("garageDoors", [garageDoor, garageBackDoor, garageHouseDoor], type="door", group="Doors", label="Garage doors")
    doorbellButton = Sensor("doorbellButton", gpio1, 3, interrupt=doorbellInterrupt)
    doorbell = OneShotControl("doorbell", None, duration=10, type="sound", group="Doors", label="Doorbell", event=stateChangeEvent)

    # Weather
    anemometer = Sensor("anemometer", gpio1, addr=windSpeedAddr)
    windVane = Sensor("windVane", gpio1, addr=windDirAddr)
    windInterface = WindInterface("windInterface", None, anemometer=anemometer, windVane=windVane)
    windSpeed = Sensor("windSpeed", windInterface, addr="speed", type="MPH", group="Weather", label="Wind speed")
    windDir = Sensor("windDir", windInterface, addr="dir", type="Deg", group="Weather", label="Wind direction")

    rainGauge = Sensor("rainGauge", gpio1, addr=rainGaugeAddr)
    rainInterface = RainInterface("rainInterface", fileInterface, rainGauge=rainGauge)
    rainMinute = Sensor("rainMinute", rainInterface, "minute", type="in", group="Weather", label="Rain per minute")
    rainHour = Sensor("rainHour", rainInterface, "hour", type="in", group="Weather", label="Rain last hour")
    rainDay = Sensor("rainDay", rainInterface, "today", type="in", group="Weather", label="Rain today")
    rainReset = Control("rainReset ", rainInterface, "reset")

    # Tasks
    hotWaterRecirc = Task("hotWaterRecirc", SchedTime(hour=[5], minute=[0]), recircPump, 1, endTime=SchedTime(hour=[23], minute=[0]), group="Water")
    # hotWaterRecircOn = Task("hotWaterRecircOn", SchedTime(hour=[05], minute=[0]), recircPump, 1)
    # hotWaterRecircOff = Task("hotWaterRecircOff", SchedTime(hour=[23], minute=[0]), recircPump, 0)
    rainResetTask = Task("rainResetTask", SchedTime(hour=0, minute=0), rainReset, 0, enabled=True)

    # Schedule
    schedule = Schedule("schedule", tasks=[hotWaterRecirc, rainResetTask])

    # Resources
    resources = Collection("resources", resources=[recircPump, sculptureLights, doorbell,
                                                   garageDoor, garageBackDoor, garageHouseDoor, garageDoors,
                                                   doorbellButton,
                                                   windSpeed, windDir, rainMinute, rainHour, rainDay,
                                                   hotWaterRecirc,
                                                   ])
    restServer = RestServer("garage", resources, event=stateChangeEvent, label="Garage")

    # Start interfaces
    doorbellThread = threading.Thread(target=doorbellHandler, args=(doorbell,))
    doorbellThread.start()
    gpio0.start()
    gpio1.start()
    fileInterface.start()
    rainInterface.start()
    schedule.start()
    restServer.start()
