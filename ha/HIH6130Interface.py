import time
from ha.HAClasses import *

# HIH-6130/6131 humidity sensor

class HIH6130Interface(HAInterface):
    def __init__(self, name, interface, addr=0x27):
        HAInterface.__init__(self, name, interface)
        self.addr = addr

    def read(self, addr):
        debug('debugHIH6130', self.name, "read", addr)
        try:
            self.interface.writeQuick(self.addr)
            time.sleep(0.050)
            d = self.interface.readBlock((self.addr, 0), 4)
            status = (d[0] & 0xc0) >> 6
            humidity = (((d[0] & 0x3f) << 8) + d[1])*100/16383
            return humidity
        except:
            return 0

