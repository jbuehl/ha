
import smbus
from ha.HAClasses import *

class I2CInterface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)
        self.bus = smbus.SMBus(self.interface)

    def read(self, addr):
        try:
            if debugI2C: log(self.name, "readByte", addr)
            return self.bus.read_byte_data(*addr)
        except:
            return 0

    def readWord(self, addr):
        try:
            if debugI2C: log(self.name, "readWord", addr)
            return self.bus.read_word_data(*addr)
        except:
            return 0

    def write(self, addr, value):
        if debugI2C: log(self.name, "writeByte", addr, value)
        self.bus.write_byte_data(*addr+(value,))

    def writeWord(self, addr, value):
        if debugI2C: log(self.name, "writeWord", addr, value)
        self.bus.write_word_data(*addr+(value,))


