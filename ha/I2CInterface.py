
import smbus
from ha.HAClasses import *

class HAI2CInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)
        self.bus = smbus.SMBus(self.interface)

    def read(self, theAddr):
        try:
            if debugI2C: log(self.name, "readByte", theAddr)
            return self.bus.read_byte_data(*theAddr)
        except:
            return 0

    def readWord(self, theAddr):
        try:
            if debugI2C: log(self.name, "readWord", theAddr)
            return self.bus.read_word_data(*theAddr)
        except:
            return 0

    def write(self, theAddr, theValue):
        if debugI2C: log(self.name, "writeByte", theAddr, theValue)
        self.bus.write_byte_data(*theAddr+(theValue,))

    def writeWord(self, theAddr, theValue):
        if debugI2C: log(self.name, "writeWord", theAddr, theValue)
        self.bus.write_word_data(*theAddr+(theValue,))


