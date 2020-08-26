
weatherSampleRate = 10

import time
import threading
import math
import bme680
from ha import *

# BME-680 temperature, humidity, pressure, VOC sensor

class BME680Interface(Interface):
    def __init__(self, name, interface=None, addr=0x77, event=None):
        Interface.__init__(self, name, interface, event=event)
        self.addr = addr
        self.lock = threading.Lock()
        self.sensor = bme680.BME680(self.addr)
        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)
        # self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        # self.sensor.set_gas_heater_temperature(320)
        # self.sensor.set_gas_heater_duration(150)
        # self.sensor.select_gas_heater_profile(0)
        def sample():
            while True:
                with self.lock:
                    while not self.sensor.get_sensor_data():
                        time.sleep(.1)
                time.sleep(weatherSampleRate)
        sampleThread = LogThread(target=sample)
        sampleThread.start()

    def read(self, addr):
        with self.lock:
            if addr == "temp":
                value = self.sensor.data.temperature * 9/5 + 32
            elif addr == "humidity":
                value = self.sensor.data.humidity
            elif addr == "dewpoint":
                # https://en.wikipedia.org/wiki/Dew_point
                b = 17.62
                c = 243.12
                g = math.log(self.sensor.data.humidity / 100) + ((b * self.sensor.data.temperature) / (c + self.sensor.data.temperature))
                value = (c * g) / (b - g) * 9/5 + 32
            elif addr == "barometer":
                value = self.sensor.data.pressure  * 0.029529983071445
            elif addr == "voc":
                if self.sensor.data.heat_stable:
                    value = self.sensor.data.gas_resistance
                else:
                    value = 0
            else:
                value = 0
        debug('debugBME680', self.name, addr, value)
        return round(value, 2)
