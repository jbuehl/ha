
import threading
import time
import json
from ha import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.ads1015Interface import *
from ha.interfaces.fileInterface import *
from ha.controls.electricalSensors import *
from ha.controls.carchargerControl import *
from ha.rest.restServer import *

# ADC parameters
adcType = 0x01 #__IC_ADS1115
adcAddr = 0x48
adcGain = 4096
adcSps = 860

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    # i2cInterface = I2CInterface("i2cInterface", bus=1, event=stateChangeEvent)
    ads1015Interface = ADS1015Interface("ads1015Interface", addr=adcAddr, gain=adcGain, sps=adcSps, ic=adcType)
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"carcharger.state", event=stateChangeEvent, initialState={"maxChargingCurrent": 30})
    maxChargingCurrent = MultiControl("maxChargingCurrent", fileInterface, "maxChargingCurrent", values=[30, 24, 18, 15, 10, 6],
                                  group=["Car"], label="Max charging current")

    # Sensors
    pilotVoltage = VoltageSensor("pilotVoltage", ads1015Interface, 0, voltageFactor=3, group=["Car"], label="Pilot voltage", type="V", event=stateChangeEvent)
    chargingCurrent = CurrentSensor("loads.carcharger.current", ads1015Interface, 1, currentFactor=10, threshold=.1,
                                group=["Car", "Power", "Loads"], label="Car charger current", type="A", event=stateChangeEvent)
    chargingPower = PowerSensor("loads.carcharger.power", currentSensor=chargingCurrent, voltage=240,
                                group=["Car", "Power", "Loads"], label="Car charger", type="KVA", event=stateChangeEvent)

    # Charger control
    charger = CarChargerControl("charger", None, pilotVoltage, chargingPower, maxChargingCurrent, group="Car", label="Car charger", type="charger", event=stateChangeEvent)

    # Schedules
    carChargerEnabledTask = Task("carChargerEnabledTask", SchedTime(hour=[20], minute=[0]), charger, 1)
    carChargerDisabledTask = Task("carChargerDisabledTask", SchedTime(hour=[10], minute=[0]), charger, 0)
    schedule = Schedule("schedule", [carChargerEnabledTask, carChargerDisabledTask])

    # Resources
    resources = Collection("resources", [pilotVoltage, chargingCurrent, chargingPower, charger, maxChargingCurrent,
                                         carChargerEnabledTask, carChargerDisabledTask,
                                        ])
    restServer = RestServer("carcharger", resources, event=stateChangeEvent, label="Car charger")

    # Start interfaces
#    carCharger.start()
    fileInterface.start()
    schedule.start()
    restServer.start()
