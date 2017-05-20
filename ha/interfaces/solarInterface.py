from ha import *

#    interface - an instance of a fileInterface that contains solar performance data

#    addr - a tuple consisting of
#        device type - "inverters" | "optimizers"
#        device ID or operator - "sum" | "avg"
#        attribute
    
class SolarInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        try:
            devices = self.interface.read(addr[0])
            value = 0
            for device in devices.values():
                value += float(device[addr[2]])
            if addr[1] == "avg":
                value /= len(devices)
            return value
        except:
            return "-"

