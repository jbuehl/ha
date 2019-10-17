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

    # Sensors
    lightsCurrent = CurrentSensor("loads.lights.current", ads1015Interface0, 0, VC25,
                                  group=["Power", "Loads"], label="Lights current", type="A", event=stateChangeEvent)
    plugsCurrent = CurrentSensor("loads.plugs.current", ads1015Interface0, 1, VC25,
                                  group=["Power", "Loads"], label="Plugs current", type="A", event=stateChangeEvent)
    appl1Current = CurrentSensor("loads.appliance1.current", ads1015Interface0, 2, VC25,
                                  group=["Power", "Loads"], label="Appliances 1 current", type="A", event=stateChangeEvent)
    cookingCurrent = CurrentSensor("loads.cooking.current", ads1015Interface0, 3, VC100,
                                  group=["Power", "Loads"], label="Cooking current", type="A", event=stateChangeEvent)
    appl2Current = CurrentSensor("loads.appliance2.current", ads1015Interface1, 0, VC25,
                                  group=["Power", "Loads"], label="Appliances 2 current", type="A", event=stateChangeEvent)
    acCurrent = CurrentSensor("loads.ac.current", ads1015Interface1, 1, VC50,
                                  group=["Power", "Loads"], label="Air conditioners current", type="A", event=stateChangeEvent)
    backhouseCurrent = CurrentSensor("loads.backhouse.current", ads1015Interface1, 2, VC25,
                                  group=["Power", "Loads"], label="Back house current", type="A", event=stateChangeEvent)
    poolCurrent = CurrentSensor("loads.pool.current", ads1015Interface1, 3, VC50,
                                  group=["Power", "Loads"], label="Pool equipment current", type="A", event=stateChangeEvent)

    lightsPower = PowerSensor("loads.lights.power", currentSensor=lightsCurrent, voltage=120,
                                  group=["Power", "Loads"], label="Lights", type="KVA", event=stateChangeEvent)
    plugsPower = PowerSensor("loads.plugs.power", currentSensor=plugsCurrent, voltage=120,
                                  group=["Power", "Loads"], label="Plugs", type="KVA", event=stateChangeEvent)
    appl1Power = PowerSensor("loads.appliance1.power", currentSensor=appl1Current, voltage=120,
                                  group=["Power", "Loads"], label="Appliances 1", type="KVA", event=stateChangeEvent)
    cookingPower = PowerSensor("loads.cooking.power", currentSensor=cookingCurrent, voltage=240,
                                  group=["Power", "Loads"], label="Cooking", type="KVA", event=stateChangeEvent)
    appl2Power = PowerSensor("loads.appliance2.power", currentSensor=appl2Current, voltage=120,
                                  group=["Power", "Loads"], label="Appliances 2", type="KVA", event=stateChangeEvent)
    acPower = PowerSensor("loads.ac.power", currentSensor=acCurrent, voltage=240,
                                  group=["Power", "Loads"], label="Air conditioners", type="KVA", event=stateChangeEvent)
    backhousePower = PowerSensor("loads.backhouse.power", currentSensor=backhouseCurrent, voltage=240,
                                  group=["Power", "Loads"], label="Back house", type="KVA", event=stateChangeEvent)
    poolPower = PowerSensor("loads.pool.power", currentSensor=poolCurrent, voltage=240,
                                  group=["Power", "Loads"], label="Pool equipment", type="KVA", event=stateChangeEvent)

    totalPower = CalcSensor("loads.stats.power", [lightsPower, plugsPower, appl1Power, cookingPower,
                                                  appl2Power,acPower, backhousePower, poolPower,
                                                  "loads.carcharger.power"], "sum", resources=cacheResources,
                                  group=["Power", "Loads"], label="Total load", type="KVA")
    # Resources
    resources = Collection("resources", [lightsCurrent, plugsCurrent, appl1Current, cookingCurrent,
                                         appl2Current, acCurrent, backhouseCurrent, poolCurrent,
                                         lightsPower, plugsPower, appl1Power, cookingPower,
                                         appl2Power, acPower, backhousePower, poolPower,
                                         totalPower
                                         ])

    # start the task to transmit resource metrics
    resourceStates = ResourceStateSensor("states", None, resources=resources, event=stateChangeEvent)
    startMetrics(resourceStates, sendMetrics, logMetrics, backupMetrics, logChanged)

    restServer = RestServer("loads", resources, event=stateChangeEvent, label="Power loads")

    # Start interfaces
    restServer.start()
