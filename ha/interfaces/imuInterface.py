import math

from ha import *

class ImuInterface(Interface):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        try:
            if addr == "Hdg":
                hdg = math.degrees(math.atan(self.interface.read("MagZ")/self.interface.read("MagX")))
                if hdg < 0:
                    hdg =+ 360
                return hdg
        except:
            raise #return "-"

