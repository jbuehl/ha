from ha import *
import threading

# analog temp sensor

class AnalogTempInterface(Interface):
    def __init__(self, name, interface):
        Interface.__init__(self, name, interface)
        self.lock = threading.Lock()

    def read(self, addr):
        debug('debugAnalogTemp', self.name, "read", addr)
        try:
            with self.lock:
                mVolts = self.interface.read(addr)
            volts = float(mVolts)/1000 + .0005
            tempC = 28.25 * (2.52 - volts)
            tempF = tempC * 9 / 5 + 32
            debug('debugAnalogTemp', self.name, "volts", volts, "tempC", tempC, "tempF", tempF)
            return tempF
        except:
            return 0

