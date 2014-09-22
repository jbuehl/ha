from ha.HAClasses import *

class HAPowerInterface(HAInterface):
    def __init__(self, theName, theInterface, powerTbl):
        HAInterface.__init__(self, theName, theInterface)
        self.powerTbl = powerTbl

    def read(self, theAddr):
        if theAddr.getState():
            return self.powerTbl[theAddr.name]
        else:
            return 0 


