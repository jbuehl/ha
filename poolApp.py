defaultConfig = {
    "spaTempTarget": 100,
}
spaTempTargetMin = 75
spaTempTargetMax = 102


import threading
import time
import json
from ha import *
from ha.interfaces.serialInterface import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.pentairInterface import *
from ha.interfaces.powerInterface import *
from ha.interfaces.owfsInterface import *
from ha.interfaces.ads1015Interface import *
from ha.interfaces.analogTempInterface import *
from ha.interfaces.valveInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.timeInterface import *
from ha.controls.tempControl import *
from ha.controls.poolControls import *
from ha.rest.restServer import *

serialConfig = {"baudrate": 9600,
                 "bytesize": serial.EIGHTBITS,
                 "parity": serial.PARITY_NONE,
                 "stopbits": serial.STOPBITS_ONE}

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    nullInterface = Interface("nullInterface", Interface("None"))
    serialInterface = SerialInterface("serialInterface", device=pentairDevice, config=serialConfig, event=stateChangeEvent)
    i2cInterface = I2CInterface("i2cInterface", bus=1, event=stateChangeEvent)
    gpioInterface0 = GPIOInterface("gpioInterface0", i2cInterface, addr=0x20, bank=0, inOut=0x00)
    gpioInterface1 = GPIOInterface("gpioInterface1", i2cInterface, addr=0x20, bank=1, inOut=0x00)
    pentairInterface = PentairInterface("pentairInterface", serialInterface)
    powerInterface = PowerInterface("powerInterface", Interface("None"), event=stateChangeEvent)
    owfsInterface = OWFSInterface("owfsInterface", event=stateChangeEvent)
    ads1015Interface = ADS1015Interface("ads1015Interface", addr=0x48)
    analogTempInterface = AnalogTempInterface("analogTempInterface", ads1015Interface)
    valveInterface = ValveInterface("valveInterface", gpioInterface1)
    timeInterface = TimeInterface("timeInterface", None, latLong=latLong)
    configInterface = FileInterface("configInterface", fileName=stateDir+"pool.state", event=stateChangeEvent, initialState=defaultConfig)

    # persistent config data
    spaTempTarget = MinMaxControl("spaTempTarget", configInterface, "spaTempTarget", spaTempTargetMin, spaTempTargetMax,
                                group="Pool", label="Spa temp set", type="tempFControl")

    # Lights
    poolLight = Control("poolLight", gpioInterface0, 2, type="light", group=["Pool", "Lights"], label="Pool light")
    spaLight = Control("spaLight", gpioInterface0, 3, type="light", group=["Pool", "Lights"], label="Spa light")
    poolLights = ControlGroup("poolLights", [poolLight, spaLight], type="light", group=["Pool", "Lights"], label="Pool and spa")

    # Temperature
    waterTemp = Sensor("waterTemp", analogTempInterface, 0, group=["Pool", "Temperature"], label="Water temp", type="tempF")
    spaTemp = Sensor("spaTemp", analogTempInterface, 1, group=["Pool", "Temperature"], label="Spa temp", type="tempF")
#    spaTemp = Sensor("spaTemp", owfsInterface, "28.556E5F070000", group=["Pool", "Temperature"], label="Spa temp", type="tempF")
    poolTemp = Sensor("poolTemp", owfsInterface, "28.B9CA5F070000", group=["Pool", "Temperature"], label="Pool temp", type="tempF")
    poolEquipTemp = Sensor("poolEquipTemp", analogTempInterface, 0, group=["Pool", "Temperature", "Weather"], label="Pool equipment temp", type="tempF")

    # Pump
    poolPump = Control("poolPump", pentairInterface, 0, group="Pool", label="Pump", type="pump")
    poolPumpSpeed = Sensor("poolPumpSpeed", pentairInterface, 1, group="Pool", label="Pump speed", type="pumpSpeed")
    poolPumpFlow = Sensor("poolPumpFlow", pentairInterface, 3, group="Pool", label="Pump flow", type="pumpFlow")

    # Accessories
    poolCleaner = Control("poolCleaner", gpioInterface0, 0, group="Pool", label="Polaris", type="cleaner")
    spaBlower = Control("spaBlower", gpioInterface0, 1, group="Pool", label="Spa blower")

    # Valves
    intakeValve = Control("intakeValve", valveInterface, 0, group="Pool", label="Intake valve", type="poolValve")
    returnValve = Control("returnValve", valveInterface, 1, group="Pool", label="Return valve", type="poolValve")
    valveMode = ControlGroup("valveMode", [intakeValve, returnValve], stateList=[[0, 1, 1, 0], [0, 1, 0, 1]], stateMode=True,
                             type="valveMode", group="Pool", label="Valve mode")

    # Heater
    poolHeater = Control("poolHeater", gpioInterface1, 2, group="Pool", label="Pool heater")
    heaterControl = TempControl("heaterControl", nullInterface, poolHeater, spaTemp, spaTempTarget, hysteresis=[1, 0], group="Pool", label="Heater control", type="tempControl")

    # Controls
    spaFill = ControlGroup("spaFill", [valveMode, poolPump], stateList=[[0, 3], [0, 4]], stateMode=True, group="Pool", label="Spa fill")
    spaFlush = ControlGroup("spaFlush", [valveMode, poolPump], stateList=[[0, 3], [0, 3]], stateMode=True, group="Pool", label="Spa flush")
    spaDrain = ControlGroup("spaDrain", [valveMode, poolPump], stateList=[[0, 2], [0, 4]], stateMode=True, group="Pool", label="Spa drain")
    poolClean = ControlGroup("poolClean", [poolCleaner, poolPump], stateList=[[0, 1], [0, 3]], stateMode=True, group="Pool", label="Pool clean")

    # Spa
    sunUp = Sensor("sunUp", timeInterface, "daylight")
    # spa light control that will only turn on if the sun is down
    spaLightNight = DependentControl("spaLightNight", nullInterface, spaLight, [(sunUp, "==", 0)])
    spa = SpaControl("spa", nullInterface, valveMode, poolPump, heaterControl, spaLightNight, spaTemp, spaTempTarget, group="Pool", label="Spa", type="spa")
    # spa light control that will only turn on if the sun is down and the spa is on
    spaLightNightSpa = DependentControl("spaLightNightSpa", nullInterface, spaLightNight, [(spa, "==", 1)])

    filterSequence = Sequence("filterSequence", [Cycle(poolPump, duration=39600, startState=1),  # filter 11 hr
                                              ], group="Pool", label="Filter daily")
    cleanSequence = Sequence("cleanSequence", [Cycle(poolClean, duration=3600, startState=1),
                                              ], group="Pool", label="Clean 1 hr")
    flushSequence = Sequence("flushSequence", [Cycle(spaFlush, duration=900, startState=1),
                                              ], group="Pool", label="Flush spa 15 min")

    # Power
    poolPumpPower = Sensor("poolPumpPower", pentairInterface, 2, type="power", group=["Pool", "Power", "Loads"], label="Pool pump")
    poolCleanerPower = Sensor("poolCleanerPower", powerInterface, poolCleaner, type="power", group=["Pool", "Power", "Loads"], label="Pool cleaner")
    spaBlowerPower = Sensor("spaBlowerPower", powerInterface, spaBlower, type="power", group=["Pool", "Power", "Loads"], label="Spa blower")
    poolLightPower = Sensor("poolLightPower", powerInterface, poolLight, type="power", group=["Pool", "Power", "Loads"], label="Pool light")
    spaLightPower = Sensor("spaLightPower", powerInterface, spaLight, type="power", group=["Pool", "Power", "Loads"], label="Spa light")

    # Schedules
    sundaySpaOnTask = Task("sundaySpaOnTask", SchedTime(year=[2016], month=[8], day=[14], hour=[16], minute=[30]), spa, 1)
    sundaySpaOffTask = Task("sundaySpaOffTask", SchedTime(year=[2016], month=[8], day=[14], hour=[18], minute=[30]), spa, 0)
    poolFilterTask = Task("poolFilterTask", SchedTime(hour=[21], minute=[0]), filterSequence, 1, group="Pool")
    poolCleanerTask = Task("poolCleanerTask", SchedTime(hour=[8], minute=[1]), cleanSequence, 1, group="Pool")
    flushSpaTask = Task("flushSpaTask", SchedTime(hour=[9], minute=[2]), flushSequence, 1, group="Pool")
    spaLightOnSunsetTask = Task("spaLightOnSunsetTask", SchedTime(event="sunset"), spaLightNightSpa, 1)
    schedule = Schedule("schedule", [sundaySpaOnTask, sundaySpaOffTask, poolFilterTask, poolCleanerTask, flushSpaTask, spaLightOnSunsetTask])

    # Resources
    resources = Collection("resources", [poolLight, spaLight, poolLights,
                                        waterTemp, poolTemp, spaTemp, poolEquipTemp,
                                        poolPump, poolCleaner, poolClean, intakeValve, returnValve,
                                        valveMode, spaFill, spaFlush, spaDrain, poolHeater, spaBlower,
                                        poolPumpSpeed, poolPumpFlow,
                                        spa, spaTempTarget, heaterControl,
                                        poolPumpPower, poolCleanerPower, spaBlowerPower, poolLightPower, spaLightPower,
                                        filterSequence, cleanSequence, flushSequence,
                                        poolFilterTask, poolCleanerTask, flushSpaTask,
                                        ])
    restServer = RestServer("pool", resources, event=stateChangeEvent, label="Pool")

    # Start interfaces
    configInterface.start()
    gpioInterface0.start()
    gpioInterface1.start()
    pentairInterface.start()
    schedule.start()
    restServer.start()
