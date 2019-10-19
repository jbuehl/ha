# Monitor current sensors for each circuit and log the average VA for each circuit

logDir = "/data/loads/"
sendMetrics = False
logMetrics = True
logChanged = False
backupMetrics = True
restWatch = ["carcharger"]

import time
import json
from ha.interfaces.i2cInterface import *
from ha.interfaces.ads1015Interface import *
from ha.interfaces.fileInterface import *
from ha.controls.electricalSensors import *
from ha.metrics import *
from ha.rest.restServer import *
from ha.rest.restProxy import *

# ADC parameters
adcType = 0x00 #__IC_ADS1015
adcGain = 4096  # +/- 4.096V
adcSps = 250  # 250 samples per second

# Current sensor multipliers
VC10 = 2
VC25 = 5
VC50 = 10
VC100 = 20

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # start the cache to listen for services on other servers
    cacheResources = Collection("cacheResources")
    restCache = RestProxy("restProxy", cacheResources, watch=restWatch, event=stateChangeEvent)
    restCache.start()


    # Interfaces
    i2cInterface = I2CInterface("i2cInterface", bus=1, event=stateChangeEvent)
    ads1015Interface0 = ADS1015Interface("ads1015Interface0", addr=0x48, gain=adcGain, sps=adcSps, ic=adcType)
    ads1015Interface1 = ADS1015Interface("ads1015Interface1", addr=0x49, gain=adcGain, sps=adcSps, ic=adcType)
    stateInterface = FileInterface("stateInterface", fileName=stateDir+"power.state")

    # Sensors
    lightsCurrent = CurrentSensor("loads.lights.current", ads1015Interface0, 0, VC25, threshold=.01,
                                  group=["Power", "Loads"], label="Lights current", type="A", event=stateChangeEvent)
    plugsCurrent = CurrentSensor("loads.plugs.current", ads1015Interface0, 1, VC25, threshold=.01,
                                  group=["Power", "Loads"], label="Plugs current", type="A", event=stateChangeEvent)
    appl1Current = CurrentSensor("loads.appliance1.current", ads1015Interface0, 2, VC25, threshold=.01,
                                  group=["Power", "Loads"], label="Appliances 1 current", type="A", event=stateChangeEvent)
    cookingCurrent = CurrentSensor("loads.cooking.current", ads1015Interface0, 3, VC100, threshold=1,
                                  group=["Power", "Loads"], label="Cooking current", type="A", event=stateChangeEvent)
    appl2Current = CurrentSensor("loads.appliance2.current", ads1015Interface1, 0, VC25, threshold=.01,
                                  group=["Power", "Loads"], label="Appliances 2 current", type="A", event=stateChangeEvent)
    acCurrent = CurrentSensor("loads.ac.current", ads1015Interface1, 1, VC50, threshold=1,
                                  group=["Power", "Loads"], label="Air conditioners current", type="A", event=stateChangeEvent)
    backhouseCurrent = CurrentSensor("loads.backhouse.current", ads1015Interface1, 2, VC25, threshold=.01,
                                  group=["Power", "Loads"], label="Back house current", type="A", event=stateChangeEvent)
    poolCurrent = CurrentSensor("loads.pool.current", ads1015Interface1, 3, VC50, threshold=.1,
                                  group=["Power", "Loads"], label="Pool equipment current", type="A", event=stateChangeEvent)

    lightsPower = PowerSensor("loads.lights.power", currentSensor=lightsCurrent, voltage=120, threshold=1,
                                  group=["Power", "Loads"], label="Lights", type="KVA", event=stateChangeEvent)
    plugsPower = PowerSensor("loads.plugs.power", currentSensor=plugsCurrent, voltage=120, threshold=1,
                                  group=["Power", "Loads"], label="Plugs", type="KVA", event=stateChangeEvent)
    appl1Power = PowerSensor("loads.appliance1.power", currentSensor=appl1Current, voltage=120, threshold=1,
                                  group=["Power", "Loads"], label="Appliances 1", type="KVA", event=stateChangeEvent)
    cookingPower = PowerSensor("loads.cooking.power", currentSensor=cookingCurrent, voltage=240, threshold=100,
                                  group=["Power", "Loads"], label="Cooking", type="KVA", event=stateChangeEvent)
    appl2Power = PowerSensor("loads.appliance2.power", currentSensor=appl2Current, voltage=120, threshold=1,
                                  group=["Power", "Loads"], label="Appliances 2", type="KVA", event=stateChangeEvent)
    acPower = PowerSensor("loads.ac.power", currentSensor=acCurrent, voltage=240, threshold=100,
                                  group=["Power", "Loads"], label="Air conditioners", type="KVA", event=stateChangeEvent)
    backhousePower = PowerSensor("loads.backhouse.power", currentSensor=backhouseCurrent, voltage=240, threshold=10,
                                  group=["Power", "Loads"], label="Back house", type="KVA", event=stateChangeEvent)
    poolPower = PowerSensor("loads.pool.power", currentSensor=poolCurrent, voltage=240, threshold=10,
                                  group=["Power", "Loads"], label="Pool equipment", type="KVA", event=stateChangeEvent)

    load = CalcSensor("loads.stats.power", [lightsPower, plugsPower, appl1Power, cookingPower,
                                                  appl2Power,acPower, backhousePower, poolPower,
                                                  "loads.carcharger.power"], "sum", resources=cacheResources,
                                  group=["Power", "Loads"], label="Load", type="KVA")

    lightsEnergy = EnergySensor("loads.lights.dailyEnergy", powerSensor=lightsPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Lights daily energy", type="KWh", event=stateChangeEvent)
    plugsEnergy = EnergySensor("loads.plugs.dailyEnergy", powerSensor=plugsPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Plugs daily energy", type="KWh", event=stateChangeEvent)
    appl1Energy = EnergySensor("loads.appliance1.dailyEnergy", powerSensor=appl1Power, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Appliances 1 daily energy", type="KWh", event=stateChangeEvent)
    cookingEnergy = EnergySensor("loads.cooking.dailyEnergy", powerSensor=cookingPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Cooking daily energy", type="KWh", event=stateChangeEvent)
    appl2Energy = EnergySensor("loads.appliance2.dailyEnergy", powerSensor=appl2Power, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Appliances 2 daily energy", type="KWh", event=stateChangeEvent)
    acEnergy = EnergySensor("loads.ac.dailyEnergy", powerSensor=acPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Air conditioners daily energy", type="KWh", event=stateChangeEvent)
    backhouseEnergy = EnergySensor("loads.backhouse.dailyEnergy", powerSensor=backhousePower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Back house daily energy", type="KWh", event=stateChangeEvent)
    poolEnergy = EnergySensor("loads.pool.dailyEnergy", powerSensor=poolPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Pool equipment daily energy", type="KWh", event=stateChangeEvent)
    carchargerEnergy = EnergySensor("loads.carcharger.dailyEnergy", powerSensor="loads.carcharger.power", resources=cacheResources, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Car charger daily energy", type="KWh", event=stateChangeEvent)

    dailyEnergy = CalcSensor("loads.stats.dailyEnergy", [lightsEnergy, plugsEnergy, appl1Energy, cookingEnergy,
                                                  appl2Energy,acEnergy, backhouseEnergy, poolEnergy,
                                                  carchargerEnergy], "sum", resources=cacheResources,
                                  group=["Power", "Loads"], label="Daily load", type="KWh")

    # Tasks
    energySensors = ControlGroup("energySensors", None, [lightsEnergy, plugsEnergy, appl1Energy, cookingEnergy,
                                                          appl2Energy, acEnergy, backhouseEnergy, poolEnergy, carchargerEnergy])
    resetEnergySensorsTask = Task("resetEnergySensorsTask", SchedTime(hour=0, minute=0), energySensors, 0.0, enabled=True, group="Power")
    schedule = Schedule("schedule", tasks=[resetEnergySensorsTask])

    # Resources
    resources = Collection("resources", [lightsCurrent, plugsCurrent, appl1Current, cookingCurrent,
                                         appl2Current, acCurrent, backhouseCurrent, poolCurrent,
                                         lightsPower, plugsPower, appl1Power, cookingPower,
                                         appl2Power, acPower, backhousePower, poolPower,
                                         lightsEnergy, plugsEnergy, appl1Energy, cookingEnergy,
                                         appl2Energy, acEnergy, backhouseEnergy, poolEnergy, carchargerEnergy,
                                         load, dailyEnergy, resetEnergySensorsTask,
                                         ])

    # start the task to transmit resource metrics
    resourceStates = ResourceStateSensor("states", None, resources=resources, event=stateChangeEvent)
    startMetrics(resourceStates, sendMetrics, logMetrics, backupMetrics, logChanged)

    restServer = RestServer("loads", resources, event=stateChangeEvent, label="Power loads")

    # Start interfaces
    schedule.start()
    restServer.start()
