from ha.HAClasses import *

# analog temp sensor

class AnalogTempInterface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)

    def read(self, addr):
        debug('debugAnalogTemp', self.name, "read", addr)
        try:
            volts = float(self.interface.read(addr))/1000 + .0005
            tempC = 28.25 * (2.52 - volts)
            tempF = tempC * 9 / 5 + 32
            debug('debugAnalogTemp', self.name, "volts", volts, "tempC", tempC, "tempF", tempF)
            return tempF
        except:
            return 0

