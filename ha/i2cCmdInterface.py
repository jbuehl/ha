
import subprocess
from ha import *

class I2CCmdInterface(HAInterface):
    def __init__(self, name, interface=None, event=None, bus=0):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.bus = bus

    def read(self, addr):
        try:
            debug('debugI2C', self.name, "readByte", addr)
            return int(subprocess.check_output("i2cget -y %d %d %d b"%(self.bus, addr[0], addr[1]),shell=True),16)
        except:
            return 0

    def readWord(self, addr):
        try:
            debug('debugI2C', self.name, "readWord", addr)
            return int(subprocess.check_output("i2cget -y %d %d %d w"%(self.bus, addr[0], addr[1]),shell=True),16)
        except:
            return 0

    def write(self, addr, value):
        debug('debugI2C', self.name, "writeByte", addr, value)
        subprocess.check_output("i2cset -y %d %d %d %d b"%(self.bus, addr[0], addr[1], value),shell=True)

    def writeWord(self, addr, value):
        debug('debugI2C', self.name, "writeWord", addr, value)
        subprocess.check_output("i2cset -y %d %d %d %d w"%(self.bus, addr[0], addr[1], value),shell=True)

