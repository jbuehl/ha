
import threading
import time
import json
from ha import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.ads1015Interface import *
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
    i2cInterface = I2CInterface("i2cInterface", bus=1, event=stateChangeEvent)
    ads1015Interface = ADS1015Interface("ads1015Interface", addr=adcAddr, gain=adcGain, sps=adcSps, ic=adcType)
    
    # Sensors
    pilotVoltage = VoltageSensor("pilotVoltage", ads1015Interface, 0, group=["Car"], label="Pilot voltage", type="V")
    chargingCurrent = CurrentSensor("chargingCurrent", ads1015Interface, 1, group=["Car", "Power", "Loads"], label="Charging current", type="KVA")

    # Spa
    charger = CarChargerControl("charger", None, pilotVoltage, chargingCurrent, event=stateChangeEvent, group="Car", label="Car charger", type="charger")

    # Schedules
    carChargerEnabledTask = Task("carChargerEnabledTask", SchedTime(hour=[20], minute=[0]), charger, 1)
    carChargerDisabledTask = Task("carChargerDisabledTask", SchedTime(hour=[10], minute=[0]), charger, 0)
    schedule = Schedule("schedule", [carChargerEnabledTask, carChargerDisabledTask])

    # Resources
    resources = Collection("resources", [pilotVoltage, chargingCurrent, charger,
                                         carChargerEnabledTask, carChargerDisabledTask,
                                        ])
    restServer = RestServer("carcharger", resources, event=stateChangeEvent, label="Car charger")

    # Start interfaces
#    carCharger.start()
    schedule.start()
    restServer.start()

