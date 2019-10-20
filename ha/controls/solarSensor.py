from ha import *

class SolarSensor(Sensor):
    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
        Sensor.__init__(self, name, interface=interface, addr=addr, group=group, type=type, label=label, location=location)
        debug("debugSolar", "creating", name)
        self.className = "Sensor"

    def getState(self):
        try:
            (deviceType, deviceName, deviceAttr) = self.addr.split(".")
            deviceValues = self.interface.read(deviceType)
            return float(deviceValues[deviceName][deviceAttr])
        except:
            return 0.0
