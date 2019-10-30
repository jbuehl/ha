import time
import bme680
from ha import *

# BME-680 temperature, humidity, pressure, VOC sensor

class BME680Interface(Interface):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface=None, addr=0x77, event=None):
        Interface.__init__(self, name, interface, event=event)
        self.addr = addr
        self.sensor = bme680.BME680(self.addr)
        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)
        self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.sensor.set_gas_heater_temperature(320)
        self.sensor.set_gas_heater_duration(150)
        self.sensor.select_gas_heater_profile(0)

    def read(self, addr):
        debug('debugBME680', self.name, "read", addr)
        if addr == "temp":
            return self.sensor.data.temperature
        elif addr == "humidity":
            return self.sensor.data.humidity
        elif addr == "dewpoint":
            return self.sensor.data.temperature - (100 - self.sensor.data.humidity) / 5
        elif addr == "barometer":
            return self.sensor.data.pressure  * 0.029529983071445
        elif addr == "voc":
            if self.sensor.data.heat_stable:
                return self.sensor.data.gas_resistance
            else:
                return 0
        else:
            return 0
