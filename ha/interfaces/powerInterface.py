from ha import *

class PowerInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def read(self, theAddr):
        if theAddr.getState():
            return powerTbl[theAddr.name]
        else:
            return 0 


