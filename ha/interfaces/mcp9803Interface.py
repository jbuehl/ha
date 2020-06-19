from ha import *

# MCP9803 temp sensor

class MCP9803Interface(Interface):
    def __init__(self, name, interface):
        Interface.__init__(self, name, interface)

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        try:
            self.interface.write((addr, 1), 0xe1) # 12 bit mode + one shot
            t = self.interface.readWord((addr, 0))
            return (float(((t&0x00ff)<<4) | ((t&0xf000)>>12)) * .0625) * 9 / 5 + 32
        except:
            return 0

