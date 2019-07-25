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
        self.className = "Sensor"

    def getState(self):
        try:
            (deviceType, deviceName, deviceAttr) = self.addr.split(".")
            deviceValues = self.interface.read(deviceType)
            return float(deviceValues[deviceName][deviceAttr])
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
        resources.addRes(SolarSensor("solar.inverters."+inverter+".power", fileInterface, "inverters."+inverter+".Pac",
            group=["Power", "Solar", "Inverters"], type="KW", label=inverter+" power", location=inverters[inverter]))
        resources.addRes(SolarSensor("solar.inverters."+inverter+".dailyEnergy", fileInterface, "inverters."+inverter+".Eday",
            group=["Power", "Solar", "Inverters"], type="KWh", label="Inverter "+inverter+" daily energy", location=inverters[inverter]))
    for optimizer in optimizers.keys():
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".power", fileInterface, "optimizers."+optimizer+".Pdc",
            group=["Power", "Solar", "Optimizers"], type="W", label=optimizer+" power", location=optimizers[optimizer]))
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".panelCurrent", fileInterface, "optimizers."+optimizer+".Imod",
            group=["Power", "Solar", "Optimizers"], type="A", label=optimizer+" panel current", location=optimizers[optimizer]))
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".panelVoltage", fileInterface, "optimizers."+optimizer+".Vmod",
            group=["Power", "Solar", "Optimizers"], type="V", label=optimizer+" panel voltage", location=optimizers[optimizer]))
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".temp", fileInterface, "optimizers."+optimizer+".Temp",
            group=["Power", "Solar", "Optimizers"], type="tempC", label=optimizer+" temp", location=optimizers[optimizer]))
        resources.addRes(SolarSensor("solar.optimizers."+optimizer+".dailyEnergy", fileInterface, "optimizers."+optimizer+".Eday",
            group=["Power", "Solar", "Optimizers"], type="KWh", label="Optimizer "+optimizer+" daily energy", location=optimizers[optimizer]))

    # Temperature
    resources.addRes(SolarSensor("solar.inverters.stats.avgTemp", fileInterface, "inverters.stats.Temp",
        group=["Power", "Solar", "Temperature"], label="Inverter temp", type="tempC"))
    resources.addRes(SolarSensor("solar.optimizers.stats.avgTemp", fileInterface, "optimizers.stats.Temp",
        group=["Power", "Solar", "Temperature"], label="Roof temp", type="tempC"))

    # Solar stats
    resources.addRes(SolarSensor("solar.inverters.stats.avgVoltage", fileInterface, "inverters.stats.Vac",
        group=["Power", "Solar"], label="Current voltage", type="V"))
    resources.addRes(SolarSensor("solar.inverters.stats.power", fileInterface, "inverters.stats.Pac",
        group=["Power", "Solar"], label="Current power", type="KW"))
    resources.addRes(SolarSensor("solar.inverters.stats.dailyEnergy", fileInterface, "inverters.stats.Eday",
        group=["Power", "Solar"], label="Energy today", type="KWh"))
    resources.addRes(SolarSensor("solar.inverters.stats.lifetimeEnergy", fileInterface, "inverters.stats.Etot",
        group=["Power", "Solar"], label="Lifetime energy", type="MWh"))

    # Start interfaces
    fileInterface.start()
    solarInterface.start()
    restServer = RestServer("solar", resources, event=stateChangeEvent, label="Solar")
    restServer.start()
