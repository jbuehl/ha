
import smbus
from ha.HAClasses import *

class I2CInterface(HAInterface):
    def __init__(self, name, interface=None, event=None, bus=0):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.bus = smbus.SMBus(bus)

    def read(self, addr):
        try:
            debug('debugI2C', self.name, "readByte", addr)
            return self.bus.read_byte_data(*addr)
        except:
            return 0

    def readWord(self, addr):
        try:
            debug('debugI2C', self.name, "readWord", addr)
            return self.bus.read_word_data(*addr)
        except:
            return 0

    def write(self, addr, value):
        debug('debugI2C', self.name, "writeByte", addr, value)
        self.bus.write_byte_data(*addr+(value,))

    def writeWord(self, addr, value):
        debug('debugI2C', self.name, "writeWord", addr, value)
        self.bus.write_word_data(*addr+(value,))


