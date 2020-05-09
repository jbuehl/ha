
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
from ha.interfaces.modbusInterface import *
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

class RenologySensor(Sensor):
    def __init__(self, name, interface, addr, factor=1.0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.factor = factor

    def getState(self):
        state = self.interface.read(self.addr)
        if state:
            return float(state) * self.factor
        else:
            return 0.0

chargerParams = {
    0xe005: ("Over-voltage threshold", "deciVolts"),
    0xe006: ("Charging voltage limit", "deciVolts"),
    0xe007: ("Equalizing charging voltage", "deciVolts"),
    0xe008: ("Boost charging voltage", "deciVolts"),
    0xe009: ("Floating charging voltage", "deciVolts"),
    0xe00A: ("Boost charging recovery voltage", "deciVolts"),
    0xe00B: ("Over-discharge recovery voltage", "deciVolts"),
    0xe00C: ("Under-voltage warning level", "deciVolts"),
    0xe00D: ("Over-discharge voltage", "deciVolts"),
    0xe00E: ("Discharging limit voltage", "deciVolts"),
    0xe010: ("Over-discharge time delay", "sensor"),
    0xe011: ("Equalizing charging time", "sensor"),
    0xe012: ("Boost charging time", "sensor"),
    0xe013: ("Equalizing charging interval", "sensor"),
    0xe014: ("Temperature compensation factor", "sensor"),
}

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1)
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    gpio0 = MCP23017Interface("gpio0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = MCP23017Interface("gpio1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(MCP23017Interface.IPOL, 0x08)])
    led = LedInterface("led", gpio0)
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"garage.state", event=stateChangeEvent)
    modbusInterface = ModbusInterface("modbusInterface", device="/dev/ttyUSB0", event=stateChangeEvent)

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

    # backup power
    backupSolarVoltage = RenologySensor("backup.solar.voltage", modbusInterface, 0x0107, 0.1, type="V", group=["Power", "Backup"], label="Backup solar voltage")
    backupSolarCurrent = RenologySensor("backup.solar.current", modbusInterface, 0x0108, .01, type="A", group=["Power", "Backup"], label="Backup solar current")
    backupSolarPower = RenologySensor("backup.solar.power", modbusInterface, 0x0109, 1.0, type="W", group=["Power", "Backup"], label="Backup solar power")
    backupLoadVoltage = RenologySensor("backup.load.voltage", modbusInterface, 0x0104, 0.1, type="V", group=["Power", "Backup"], label="Backup load voltage")
    backupLoadCurrent = RenologySensor("backup.load.current", modbusInterface, 0x0105, .01, type="A", group=["Power", "Backup"], label="Backup load current")
    backupLoadPower = RenologySensor("backup.load.power", modbusInterface, 0x0106, 1.0, type="W", group=["Power", "Backup"], label="Backup load power")
    backupBatteryVoltage = RenologySensor("backup.battery.voltage", modbusInterface,0x0101, 0.1, type="V", group=["Power", "Backup"], label="Backup battery voltage")
    backupBatteryCharge = RenologySensor("backup.battery.charge", modbusInterface, 0x0100, 1.0, type="battery", group=["Power", "Backup"], label="Backup battery charge")
    backupBatteryCapacity = RenologySensor("backup.battery.capacity", modbusInterface, 0xe002, 1.0, type="AH", group=["Backup"], label="Backup battery capacity")
    backupChargeMode = RenologySensor("backup.chargeMode", modbusInterface, 0x0120, 1.0, type="chargeMode", group=["Power", "Backup"], label="Backup charge mode")
    backupSolarDailyEnergy = RenologySensor("backup.solar.dailyEnergy", modbusInterface, 0x0113, 1.0, type="KWh", group=["Power", "Backup"], label="Backup solar today")
    backupLoadDailyEnergy = RenologySensor("backup.load.dailyEnergy", modbusInterface, 0x0114, 1.0, type="KWh", group=["Power", "Backup"], label="Backup load today")

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
                                                   backupSolarVoltage, backupSolarCurrent, backupSolarPower,
                                                   backupLoadVoltage, backupLoadCurrent, backupLoadPower,
                                                   backupBatteryVoltage, backupBatteryCharge, backupChargeMode,
                                                   backupSolarDailyEnergy, backupLoadDailyEnergy,
                                                   backupBatteryCapacity,
                                                   ])

    # Renology charge controller parameters
    for param in list(chargerParams.keys()):
        resources.addRes(RenologySensor("backup.charger."+str(param), modbusInterface, param, 1.0, type=chargerParams[param][1], group=["Backup"], label=chargerParams[param][0]))

    restServer = RestServer("garage", resources, event=stateChangeEvent, label="Garage")

    # Start interfaces
    doorbellThread = threading.Thread(target=doorbellHandler, args=(doorbell,))
    doorbellThread.start()
    gpio0.start()
    gpio1.start()
    fileInterface.start()
    modbusInterface.start()
    schedule.start()
    restServer.start()
