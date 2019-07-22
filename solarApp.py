from ha import *
from ha.interfaces.fileInterface import *
from ha.interfaces.solarInterface import *
from ha.rest.restServer import *

inverters = {
"7F104A16": (868, 310),
"7F104920": (868, 380),
}

optimizers = {
"1016AB88": (824, 437),
"100F7333": (343, 186),
"100F7195": (211, 444),
"100E3520": (420, 443),
"100F7255": (654, 520),
"100F7118": (474, 366),
"100F714E": (127, 444),
"100F74D9": (516, 366),
"1016B2BB": (824, 514),
"100E3313": (390, 366),
"100E3325": (558, 290),
"100F7220": (301, 109),
"100F71F9": (600, 366),
"100F7237": (642, 366),
"100F7408": (744, 443),
"100F72C1": (301, 186),
"100F7401": (301, 263),
"100F74DB": (385, 109),
"100F74C6": (474, 290),
"100F746B": (343, 109),
"100F74A0": (127, 367),
"100F755D": (620, 443),
"100E34EC": (662, 443),
"100F719B": (558, 366),
"100F721E": (336, 443),
"100F707C": (432, 366),
"100F71E5": (578, 520),
"100E3326": (378, 443),
"100F743D": (516, 290),
"100F7335": (385, 186),
"100E32F9": (169, 444),
"100F6FC5": (294, 443),
"100F747C": (704, 443),
"100F74B7": (578, 443),
}

class SolarSensor(Sensor):
    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
        Sensor.__init__(self, name, interface=interface, addr=addr, group=group, type=type, label=label, location=location)
        debug("debugSolar", "creating", name)
#        # set the specified attributes
#        self.attrNames = attrs.keys()
#        for attrName in self.attrNames:
#            setattr(self, attrName, attrs[attrName])
        self.className = "Sensor"

    def getState(self):
        try:
            (deviceType, deviceName, deviceAttr) = self.name.split(".")
            deviceValues = self.interface.read(deviceType)
            return float(deviceValues[deviceName][self.addr])
        except:
            return 0.0

#    # add selected attributes to the dictionary
#    def dict(self):
#        attrs = Sensor.dict(self)
#        try:
#            # read current parameter values
#            deviceValues = self.interface.read(self.deviceType)
#            # add values to the dictionary
#            attrs.update(dict((attrName, deviceValues[self.name][attrName]) for attrName in self.attrNames))
#        except:
#            pass
#        return attrs

#class InverterStatSensor(SolarSensor):
#    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
#        attrs = {"Temp": 0.0, "Eday": 0.0, "Eac": 0.0, "Vac": 0.0, "Etot": 0.0, "Pac": 0.0}
#        SolarSensor.__init__(self, name, attrs=attrs, interface=interface, addr=addr, group=group, type=type, label=label, location=location)
#        self.deviceType = "inverters"

#    def getState(self):
#        # return inverter statistic
#        try:
#            deviceValues = self.interface.read(self.deviceType)
#            return float(deviceValues["stats"][addr])
#        except:
#            return 0.0
#
class InverterSensor(SolarSensor):
    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
        attrs = {"Uptime": 0, "Temp": 0.0, "Eday": 0.0, "Eac": 0.0, "Vac": 0.0, "Iac": 0.0, "Freq": 0.0, "Vdc": 0.0, "Etot": 0.0, "Pmax": 0.0, "Pac": 0.0}
        SolarSensor.__init__(self, name, attrs=attrs, interface=interface, addr=addr, group=group, type=type, label=label, location=location)
        self.deviceType = "inverters"

    def getState(self):
        # return current power production
        try:
            (deviceType, deviceName, deviceAttr) = self.name.split(".")
            deviceValues = self.interface.read(deviceType)
            return float(deviceValues[deviceName][self.addr])
        except:
            return 0.0

#class InverterPowerSensor(InverterSensor):
#    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
#        InverterSensor.__init__(self, name, interface=interface, addr=addr, group=group, type=type, label=label, location=location)

#    def getState(self):
#        # return current power production
#        try:
#            deviceValues = self.interface.read(self.deviceType)
#            return float(deviceValues[self.name]["Pac"])
#        except:
#            return 0.0

#class InverterEnergySensor(InverterSensor):
#    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
#        InverterSensor.__init__(self, name, interface=interface, addr=addr, group=group, type=type, label=label, location=location)

#    def getState(self):
#        # return current energy production
#        try:
#            deviceValues = self.interface.read(self.deviceType)
#            return float(deviceValues[self.name[:-2]]["Eday"])
#        except:
#            return 0.0

class OptimizerSensor(SolarSensor):
    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
        attrs = {"Inverter": "", "Uptime": 0, "Vmod": 0.0, "Vopt": 0.0, "Imod": 0.0, "Eday": 0.0, "Temp": 0.0}
        SolarSensor.__init__(self, name, attrs=attrs, interface=interface, addr=addr, group=group, type=type, label=label, location=location)
        self.deviceType = "optimizers"

class OptimizerPowerSensor(OptimizerSensor):
    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
        OptimizerSensor.__init__(self, name, interface=interface, addr=addr, group=group, type=type, label=label, location=location)

    def getState(self):
        # return current power production = V * I
        try:
            deviceValues = self.interface.read(self.deviceType)
            return float(deviceValues[self.name]["Vmod"]) * float(deviceValues[self.name]["Imod"])
        except:
            return 0.0

class OptimizerEnergySensor(OptimizerSensor):
    def __init__(self, name, interface, addr=None, group="", type="sensor", label="", location=None):
        OptimizerSensor.__init__(self, name, interface=interface, addr=addr, group=group, type=type, label=label, location=location)

    def getState(self):
        # return current energy production
        try:
            deviceValues = self.interface.read(self.deviceType)
            return float(deviceValues[self.name[:-2]]["Eday"])
        except:
            return 0.0

if __name__ == "__main__":
    # Resources
    resources = Collection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    fileInterface = FileInterface("File", fileName=solarFileName, readOnly=True, event=stateChangeEvent)
    solarInterface = SolarInterface("Solar", fileInterface)

    # Devices
    for inverter in inverters.keys():
        resources.addRes(SolarSensor("inverters."+inverter+".Pac", fileInterface, "Pac", group=["Solar", "Inverters"], type="KW", label=inverter, location=inverters[inverter]))
        resources.addRes(SolarSensor("inverters."+inverter+".Eac", fileInterface, "Eac", group=["Solar", "Inverters"], type="KWh", label="Inverter "+inverter+" energy", location=inverters[inverter]))
    for optimizer in optimizers.keys():
        resources.addRes(SolarSensor("optimizers."+optimizer, fileInterface, group=["Optimizers"], type="W", label=optimizer, location=optimizers[optimizer]))
        resources.addRes(SolarSensor("optimizers."+optimizer+"-E", fileInterface, group=["Optimizers"], type="KWh", label="Optimizer "+optimizer+" energy", location=optimizers[optimizer]))

    # Temperature
    resources.addRes(SolarSensor("inverters.stats.Temp", fileInterface, "Temp", group=["Solar", "Temperature"], label="Inverter temp", type="tempC"))
    resources.addRes(SolarSensor("optimizers.stats.Temp", fileInterface, "Temp", group=["Solar", "Temperature"], label="Roof temp", type="tempC"))

    # Solar
    resources.addRes(SolarSensor("inverters.stats.Vac", fileInterface, "Vac", group=["Solar", "Power"], label="Current voltage", type="V"))
    resources.addRes(SolarSensor("inverters.stats.Pac", fileInterface, "Pac", group=["Solar", "Power"], label="Current power", type="KW"))
    resources.addRes(SolarSensor("inverters.stats.Eday", fileInterface, "Eday", group=["Solar", "Power"], label="Energy today", type="KWh"))
#    resources.addRes(Sensor("monthlyEnergy", solarInterface, ("stats", "", "Emonth"), group=["Solar", "Power"], label="Energy this month", type="KWh"))
#    resources.addRes(Sensor("yearlyEnergy", solarInterface, ("stats", "", "Eyear"), group=["Solar", "Power"], label="Energy this year", type="MWh"))
    resources.addRes(SolarSensor("inverters.stats.Etot", fileInterface, "Etot", group=["Solar", "Power"], label="Lifetime energy", type="MWh"))

    # Start interfaces
    fileInterface.start()
    solarInterface.start()
    restServer = RestServer("solar", resources, event=stateChangeEvent, label="Solar")
    restServer.start()
