
from ha.GPIOInterface import *
from ha.HAClasses import *

class LightInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)
        self.state = [0, 0, 0, 0]

    def read(self, theAddr):
        try:
            return self.state[theAddr]
        except:
            return 0

    def write(self, theAddr, theValue):
        self.interface.write(GPIOAddr(0,0,theAddr,1), theValue)
        self.state[theAddr] = theValue

