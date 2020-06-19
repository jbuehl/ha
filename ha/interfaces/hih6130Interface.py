import time
from math import log as ln
from ha import *

# HIH-6130/6131 humidity sensor

class HIH6130Interface(Interface):
    def __init__(self, name, interface, addr=0x27):
        Interface.__init__(self, name, interface)
        self.addr = addr

    def read(self, addr):
        debug('debugHIH6130', self.name, "read", addr)
        try:
            data = self.interface.readBlock((self.addr, 0), 4)
            status = (data[0] & 0xc0) >> 6
            humidity = ((((data[0] & 0x3f) << 8) + data[1]) * 100.0) / 16383.0
            temp = (((data[2] & 0xff) << 8) + (data[3] & 0xfc)) / 4
            tempC = (temp / 16384.0) * 165.0 - 40.0
            tempF = tempC * 1.8 + 32
            # https://en.wikipedia.org/wiki/Dew_point
            # 0C <= T <= +50C
            b = 17.368
            c = 238.88
            gamma = ln(humidity / 100) + ((b * tempC) / (c + tempC))
            dewpointC = c * (gamma) / (b - gamma)
            dewpointF = dewpointC * 1.8 + 32
            debug("debugHIH6130", "humidity:", humidity, "tempC:", tempC, "tempF:", tempF, "dewpointC:", dewpointC, "dewpointF:", dewpointF)
            if addr == "humidity":
                return humidity
            elif addr == "temp":
                return tempF
            elif addr == "dewpoint":
                return dewpointF
            else:
                return 0
        except:
            return 0

