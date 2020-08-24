# Reads SolarEdge data from a JSON file produced by se2state.py

# addr consists of a string of the form "deviceType.deviceName.deviceAttr"
#   deviceType = optimizers|inverters
#   deviceName = serial number of device
#   deviceAttr = attribute

from ha import *

class SolarSensor(Sensor):
    def __init__(self, name, interface, addr, **kwargs):
        Sensor.__init__(self, name, interface, addr, **kwargs)
        debug("debugSolar", "creating", name)
        self.className = "Sensor"

    def getState(self, missing=0.0):
        try:
            (deviceType, deviceName, deviceAttr) = self.addr.split(".")
            deviceValues = self.interface.read(deviceType)
            return float(deviceValues[deviceName][deviceAttr])
        except:
            return 0.0
