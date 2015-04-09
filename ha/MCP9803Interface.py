from ha.HAClasses import *

# MCP9803 temp sensor

class MCP9803Interface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)

    def read(self, addr):
        try:
            self.interface.write(addr, (1, 0xe1)) # 12 bit mode + one shot
            t=self.interface.readWord((addr, 0))
            tempC = (float(((t&0x00ff)<<4) | ((t&0xf000)>>12)) * .0625)
            return tempC
        except:
            return 0

