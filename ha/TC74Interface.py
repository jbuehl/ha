from ha.HAClasses import *

# TC74 temp sensor

class TC74Interface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        try:
            tempC = self.interface.read((addr, 0))
            return tempC
        except:
            return 0

