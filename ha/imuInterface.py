import math

from ha.HAClasses import *

class ImuInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        try:
            if addr == "Hdg":
                hdg = math.degrees(math.atan(self.interface.read("MagZ")/self.interface.read("MagX")))
                if hdg < 0:
                    hdg =+ 360
                return hdg
        except:
            raise #return "-"

