from ha.HAClasses import *

# TMP102 temp sensor

class TMP102Interface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        try:
            t = self.interface.readWord((addr, 0))
            return (float(((t&0x00ff)<<4) | ((t&0xf000)>>12)) * .0625) * 9 / 5 + 32
        except:
            return 0

