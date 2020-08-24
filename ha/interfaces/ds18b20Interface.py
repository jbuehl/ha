from w1thermsensor import W1ThermSensor
from ha import *

# 1wire temp sensor

class DS18B20Interface(Interface):
    def __init__(self, name, interface=None):
        Interface.__init__(self, name, interface)

    def read(self, addr):
        try:
            return float(W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, addr).get_temperature())
        except Exception as ex:
            log("ds18b20", type(ex).__name__, str(ex))
            return 0
