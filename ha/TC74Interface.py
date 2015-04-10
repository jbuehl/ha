from ha.HAClasses import *

# TC74 temp sensor

class TC74Interface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        try:
            return float(self.interface.read((addr, 0))) * 9 / 5 + 32
        except:
            return 0

