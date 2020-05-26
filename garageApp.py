
doorbellState = 0
doorbellSound = "addamsdoorbell.wav"
doorbellNotifyMsg = "Doorbell "
restWatch = ["backupPowerMonitor"]
defaultConfig = {
                "backup.solar.dailyEnergy": 0.0,
                "backup.load.dailyEnergy": 0.0,
                "backup.inverter.dailyEnergy": 0.0,
                }

import time
from ha import *
from ha.interfaces.mcp23017Interface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.owfsInterface import *
from ha.interfaces.tempInterface import *
from ha.interfaces.ledInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.modbusInterface import *
from ha.controls.electricalSensors import *
from ha.rest.restServer import *
from ha.rest.restProxy import *
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
    def __init__(self, name, interface, addr, factor=1.0, mask=0xffff, shift=0,
            group="", type="sensor", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        self.className = "Sensor"
        self.factor = factor
        self.mask = mask
        self.shift = shift

    def getState(self):
        state = self.interface.read(self.addr)
        if state:
            return float((state >> self.shift) & self.mask) * self.factor
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
    0xe010: ("Over-discharge time delay", "int"),
    0xe011: ("Equalizing charging time", "int"),
    0xe012: ("Boost charging time", "int"),
    0xe013: ("Equalizing charging interval", "int"),
    0xe014: ("Temp compensation factor", "sensor"),
}

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # start the cache to listen for services on other servers
    cacheResources = Collection("cacheResources")
    restCache = RestProxy("restProxy", cacheResources, watch=restWatch, event=stateChangeEvent)
    restCache.start()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1)
    owfs = OWFSInterface("owfs", event=stateChangeEvent)
    gpio0 = MCP23017Interface("gpio0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = MCP23017Interface("gpio1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(MCP23017Interface.IPOL, 0x08)])
    led = LedInterface("led", gpio0)
    stateInterface = FileInterface("stateInterface", fileName=stateDir+"garage.state", initialState=defaultConfig, event=stateChangeEvent)
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
    stateInterface.start()
    backupSolarVoltage = RenologySensor("backup.solar.voltage", modbusInterface, 0x0107, 0.1, type="V", group=["Power", "Backup"], label="Backup solar voltage")
    backupSolarCurrent = RenologySensor("backup.solar.current", modbusInterface, 0x0108, .01, type="A", group=["Power", "Backup"], label="Backup solar current")
    backupSolarPower = RenologySensor("backup.solar.power", modbusInterface, 0x0109, 1.0, type="W", group=["Power", "Backup"], label="Backup solar power")
    backupLoadVoltage = RenologySensor("backup.load.voltage", modbusInterface, 0x0104, 0.1, type="V", group=["Power", "Backup"], label="Backup load voltage")
    backupLoadCurrent = RenologySensor("backup.load.current", modbusInterface, 0x0105, .01, type="A", group=["Power", "Backup"], label="Backup load current")
    backupLoadPower = RenologySensor("backup.load.power", modbusInterface, 0x0106, 1.0, type="W", group=["Power", "Backup"], label="Backup load power")
    backupBatteryVoltage = RenologySensor("backup.battery.voltage", modbusInterface,0x0101, 0.1, type="V", group=["Power", "Backup"], label="Backup battery voltage")
    backupBatteryCurrent = RenologySensor("backup.battery.current", modbusInterface,0x0102, 0.01, type="A", group=["Power", "Backup"], label="Backup battery current")
    backupBatteryCharge = RenologySensor("backup.battery.charge", modbusInterface, 0x0100, 1.0, type="battery", group=["Power", "Backup"], label="Backup battery charge")
    backupBatteryCapacity = RenologySensor("backup.battery.capacity", modbusInterface, 0xe002, 1.0, type="AH", group=["Backup"], label="Backup battery capacity")
    backupChargeMode = RenologySensor("backup.chargeMode", modbusInterface, 0x0120, 1.0, type="chargeMode", group=["Power", "Backup"], label="Backup charge mode")
    backupChargerTemp = RenologySensor("backup.charger.temp", modbusInterface, 0x0103, 1.0, 0xff, 8, type="tempC", group=["Power", "Backup"], label="Backup charger temp")
    backupBatteryTemp = RenologySensor("backup.battery.temp", modbusInterface, 0x0103, 1.0, 0xff, type="tempC", group=["Power", "Backup"], label="Backup battery temp")
    backupSolarDailyEnergy = EnergySensor("backup.solar.dailyEnergy", powerSensor=backupSolarPower, persistence=stateInterface,
                                  group=["Power", "Backup"], label="Backup solar today", type="KWh", event=stateChangeEvent)
    backupLoadDailyEnergy = EnergySensor("backup.load.dailyEnergy", powerSensor=backupLoadPower, persistence=stateInterface,
                                  group=["Power", "Backup"], label="Backup load today", type="KWh", event=stateChangeEvent)
    backupInverterDailyEnergy = EnergySensor("backup.inverter.dailyEnergy", powerSensor="backupPowerMonitor.power", resources=cacheResources, persistence=stateInterface,
                                  group=["Power", "Backup"], label="Backup inverter today", type="KWh", event=stateChangeEvent)

    # Tasks
    energySensors = ControlGroup("energySensors", [backupSolarDailyEnergy, backupLoadDailyEnergy, backupInverterDailyEnergy])
    resetEnergySensors = Task("resetEnergySensors", SchedTime(hour=0, minute=0), energySensors, 0, enabled=True, group=["Power", "Backup"])
    hotWaterRecirc = Task("hotWaterRecirc", SchedTime(hour=[5], minute=[0]), recircPump, 1, endTime=SchedTime(hour=[23], minute=[0]), group="Water")

    # Schedule
    schedule = Schedule("schedule", tasks=[hotWaterRecirc, resetEnergySensors])

    # Resources
    resources = Collection("resources", resources=[recircPump, sculptureLights, doorbell,
                                                   garageDoorControl, garageDoorClosed, garageDoor,
                                                   garageBackDoor, garageHouseDoor, garageDoors,
                                                   doorbellButton,
                                                   hotWaterRecirc, garageTemp,
                                                   backupSolarVoltage, backupSolarCurrent, backupSolarPower,
                                                   backupLoadVoltage, backupLoadCurrent, backupLoadPower,
                                                   backupBatteryVoltage, backupBatteryCurrent,
                                                   backupBatteryCharge, backupChargeMode,
                                                   backupSolarDailyEnergy, backupLoadDailyEnergy, backupInverterDailyEnergy,
                                                   backupBatteryCapacity, backupChargerTemp, backupBatteryTemp,
                                                   resetEnergySensors,
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
    modbusInterface.start()
    schedule.start()
    restServer.start()
