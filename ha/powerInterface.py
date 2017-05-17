from ha import *

class HAPowerInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)

    def read(self, theAddr):
        if theAddr.getState():
            return powerTbl[theAddr.name]
        else:
            return 0 


