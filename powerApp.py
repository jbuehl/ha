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
from ha.controls.solarSensor import *
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

# inverter and optimizer locations
# coordinates are pixels relative to a particular diagram

inverters = {
# inverter 1
"7F104920": (868, 380),
# inverter 2
"7F104A16": (868, 310),
}

optimizers = {
# string 1
"100E32F9": (169, 444),
"100E3313": (390, 366),
"100E3326": (378, 443),
"100E3520": (420, 443),
"100F6FC5": (294, 443),
"100F707C": (432, 366),
"100F714E": (127, 444),
"100F7195": (211, 444),
"100F721E": (336, 443),
"100F7220": (301, 109),
"100F72C1": (301, 186),
"100F7333": (343, 186),
"100F7335": (385, 186),
"100F7401": (301, 263),
"100F746B": (343, 109),
"100F74A0": (127, 367),
"100F74DB": (385, 109),
# list for grafana
# 100E32F9|100E3313|100E3326|100E3520|100F6FC5|100F707C|100F714E|100F7195|100F721E|100F7220|100F72C1|100F7333|100F7335|100F7401|100F746B|100F74A0|100F74DB

# string 2
"100E3325": (558, 290),
"100E34EC": (662, 443),
"100F7118": (474, 366),
"100F719B": (558, 366),
"100F71E5": (578, 520),
"100F71F9": (600, 366),
"100F7237": (642, 366),
"100F7255": (654, 520),
"100F7408": (746, 443),
"100F743D": (516, 290),
"100F747C": (704, 443),
"100F74B7": (578, 443),
"100F74C6": (474, 290),
"100F74D9": (516, 366),
"100F755D": (620, 443),
"1016AB88": (824, 437),
"1016B2BB": (824, 514),
# list for grafana
# 100E3325|100E34EC|100F7118|100F719B|100F71E5|100F71F9|100F7237|100F7255|100F7408|100F743D|100F747C|100F74B7|100F74C6|100F74D9|100F755D|1016AB88|1016B2BB
}

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
    solarInterface = FileInterface("solarInterface", fileName=solarFileName, readOnly=True, event=stateChangeEvent)

    # Current sensors
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

    # Power sensors
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

    # Daily energy sensors
    stateInterface.start()
    lightsEnergy = EnergySensor("loads.lights.dailyEnergy", powerSensor=lightsPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Lights daily energy", type="KVAh", event=stateChangeEvent)
    plugsEnergy = EnergySensor("loads.plugs.dailyEnergy", powerSensor=plugsPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Plugs daily energy", type="KVAh", event=stateChangeEvent)
    appl1Energy = EnergySensor("loads.appliance1.dailyEnergy", powerSensor=appl1Power, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Appliances 1 daily energy", type="KVAh", event=stateChangeEvent)
    cookingEnergy = EnergySensor("loads.cooking.dailyEnergy", powerSensor=cookingPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Cooking daily energy", type="KVAh", event=stateChangeEvent)
    appl2Energy = EnergySensor("loads.appliance2.dailyEnergy", powerSensor=appl2Power, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Appliances 2 daily energy", type="KVAh", event=stateChangeEvent)
    acEnergy = EnergySensor("loads.ac.dailyEnergy", powerSensor=acPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Air conditioners daily energy", type="KVAh", event=stateChangeEvent)
    backhouseEnergy = EnergySensor("loads.backhouse.dailyEnergy", powerSensor=backhousePower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Back house daily energy", type="KVAh", event=stateChangeEvent)
    poolEnergy = EnergySensor("loads.pool.dailyEnergy", powerSensor=poolPower, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Pool equipment daily energy", type="KVAh", event=stateChangeEvent)
    carchargerEnergy = EnergySensor("loads.carcharger.dailyEnergy", powerSensor="loads.carcharger.power", resources=cacheResources, persistence=stateInterface,
                                  group=["Power", "Loads"], label="Car charger daily energy", type="KVAh", event=stateChangeEvent)

    dailyEnergy = CalcSensor("loads.stats.dailyEnergy", [lightsEnergy, plugsEnergy, appl1Energy, cookingEnergy,
                                                  appl2Energy,acEnergy, backhouseEnergy, poolEnergy,
                                                  carchargerEnergy], "sum", resources=cacheResources,
                                  group=["Power", "Loads"], label="Load today", type="KVAh")

    # Resources
    resources = Collection("resources", [lightsCurrent, plugsCurrent, appl1Current, cookingCurrent,
                                         appl2Current, acCurrent, backhouseCurrent, poolCurrent,
                                         lightsPower, plugsPower, appl1Power, cookingPower,
                                         appl2Power, acPower, backhousePower, poolPower,
                                         lightsEnergy, plugsEnergy, appl1Energy, cookingEnergy,
                                         appl2Energy, acEnergy, backhouseEnergy, poolEnergy, carchargerEnergy,
                                         load, dailyEnergy,
                                         ])

    # Solar devices
    for inverter in list(inverters.keys()):
        resources.addRes(SolarSensor("solar.inverters."+inverter+".power", solarInterface, "inverters."+inverter+".Pac",
            group=["Power", "Solar", "Inverters"], type="KW", label=inverter+" power", location=inverters[inverter]))
        resources.addRes(SolarSensor("solar.inverters."+inverter+".dailyEnergy", solarInterface, "inverters."+inverter+".Eday",
            group=["Power", "Solar", "Inverters"], type="KWh", label="Inverter "+inverter+" daily energy", location=inverters[inverter]))
    for optimizer in list(optimizers.keys()):
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".power", solarInterface, "optimizers."+optimizer+".Pdc",
            group=["Power", "Solar", "Optimizers"], type="W", label=optimizer+" power", location=optimizers[optimizer]))
        # resources.addRes(SolarSensor("solar.optimizers."+optimizer+".panelCurrent", solarInterface, "optimizers."+optimizer+".Imod",
        #     group=["Power", "Solar", "Optimizers"], type="A", label=optimizer+" panel current", location=optimizers[optimizer]))
        # resources.addRes(SolarSensor("solar.optimizers."+optimizer+".panelVoltage", solarInterface, "optimizers."+optimizer+".Vmod",
        #     group=["Power", "Solar", "Optimizers"], type="V", label=optimizer+" panel voltage", location=optimizers[optimizer]))
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".temp", solarInterface, "optimizers."+optimizer+".Temp",
            group=["Power", "Solar", "Optimizers"], type="tempC", label=optimizer+" temp", location=optimizers[optimizer]))
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".dailyEnergy", solarInterface, "optimizers."+optimizer+".Eday",
            group=["Power", "Solar", "Optimizers"], type="KWh", label="Optimizer "+optimizer+" daily energy", location=optimizers[optimizer]))

    # Solar temperature
    resources.addRes(SolarSensor("solar.inverters.stats.avgTemp", solarInterface, "inverters.stats.Temp",
        group=["Power", "Solar", "Temperature"], label="Inverter temp", type="tempC"))
    resources.addRes(SolarSensor("solar.optimizers.stats.avgTemp", solarInterface, "optimizers.stats.Temp",
        group=["Power", "Solar", "Temperature"], label="Roof temp", type="tempC"))

    # Solar stats
    resources.addRes(SolarSensor("solar.inverters.stats.avgVoltage", solarInterface, "inverters.stats.Vac",
        group=["Power", "Solar"], label="Voltage", type="V"))
    resources.addRes(SolarSensor("solar.inverters.stats.power", solarInterface, "inverters.stats.Pac",
        group=["Power", "Solar"], label="Solar", type="KW"))
    resources.addRes(SolarSensor("solar.inverters.stats.dailyEnergy", solarInterface, "inverters.stats.Eday",
        group=["Power", "Solar"], label="Solar today", type="KWh"))
    resources.addRes(SolarSensor("solar.inverters.stats.lifetimeEnergy", solarInterface, "inverters.stats.Etot",
        group=["Power", "Solar"], label="Solar lifetime total", type="MWh"))

    resources.addRes(CalcSensor("solar.stats.netPower", [resources["solar.inverters.stats.power"], load], "diff",
        group=["Power", "Solar"], label="Net power", type="KW-"))

    resources.addRes(CalcSensor("solar.stats.netDailyEnergy", [resources["solar.inverters.stats.dailyEnergy"], dailyEnergy], "diff",
        group=["Power", "Solar"], label="Net energy today", type="KWh-"))

    # Tasks
    energySensors = ControlGroup("energySensors", [lightsEnergy, plugsEnergy, appl1Energy, cookingEnergy,
                                                          appl2Energy, acEnergy, backhouseEnergy, poolEnergy, carchargerEnergy])
    resetEnergySensorsTask = Task("resetEnergySensorsTask", SchedTime(hour=0, minute=0), energySensors, 0, enabled=True, group="Power")
    resources.addRes(resetEnergySensorsTask)
    schedule = Schedule("schedule", tasks=[resetEnergySensorsTask])

    # start the task to transmit resource metrics
    resourceStates = ResourceStateSensor("states", None, resources=resources, event=stateChangeEvent)
    startMetrics(resourceStates, sendMetrics, logMetrics, backupMetrics, logChanged)

    restServer = RestServer("power", resources, event=stateChangeEvent, label="Power")

    # Start interfaces
    solarInterface.start()
    schedule.start()
    restServer.start()
