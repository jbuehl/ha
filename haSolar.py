from ha.HAClasses import *
from ha.dbInterface import *
from ha.solarInterface import *
from ha.loadInterface import *
from ha.restServer import *

if __name__ == "__main__":

    # Collections
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    resources.addRes(sensors)

    # Interfaces
    dbInterface = HADbInterface("DB", "solar")
    solarInterface = HASolarInterface("Solar", dbInterface)
    loadInterface = HALoadInterface("Loads", dbInterface)
    
    # Temperature
    sensors.addRes(HASensor("inverterTemp", solarInterface, ("stats", "avg", "Temp"), "Temperature", label="Inverter temp", type="tempC"))
#    sensors.addRes(HASensor("roofTemp", solarInterface, ("stats", "", "Topt"), "Temperature", label="Roof temp", type="tempC"))

    # Solar
    sensors.addRes(HASensor("currentPower", solarInterface, ("inverters", "sum", "Pac"), "Solar", label="Current power", type="KW"))
    sensors.addRes(HASensor("todaysEnergy", solarInterface, ("inverters", "sum", "Eday"), "Solar", label="Energy today", type="KWh"))
#    sensors.addRes(HASensor("monthlyEnergy", solarInterface, ("stats", "", "Emonth"), "Solar", label="Energy this month", type="KWh"))
#    sensors.addRes(HASensor("yearlyEnergy", solarInterface, ("stats", "", "Eyear"), "Solar", label="Energy this year", type="MWh"))
    sensors.addRes(HASensor("lifetimeEnergy", solarInterface, ("inverters", "sum", "Etot"), "Solar", label="Lifetime energy", type="MWh"))

    # Loads
    sensors.addRes(HASensor("lightsLoad", loadInterface, ("loads", "", "lights"), "Power", label="Lights", type="KVA"))
    sensors.addRes(HASensor("plugsLoad", loadInterface, ("loads", "", "plugs"), "Power", label="Plugs", type="KVA"))
    sensors.addRes(HASensor("appl1Load", loadInterface, ("loads", "", "appl1"), "Power", label="Appliances 1", type="KVA"))
    sensors.addRes(HASensor("appl2Load", loadInterface, ("loads", "", "appl2"), "Power", label="Appliances 2", type="KVA"))
    sensors.addRes(HASensor("cookingLoad", loadInterface, ("loads", "", "cooking"), "Power", label="Stove & oven", type="KVA"))
    sensors.addRes(HASensor("acLoad", loadInterface, ("loads", "", "ac"), "Power", label="Air conditioners", type="KVA"))
    sensors.addRes(HASensor("poolLoad", loadInterface, ("loads", "", "pool"), "Power", label="Pool equipment", type="KVA"))
    sensors.addRes(HASensor("backLoad", loadInterface, ("loads", "", "back"), "Power", label="Back house", type="KVA"))

    # Start interfaces
    dbInterface.start()
    solarInterface.start()
    restServer = RestServer(resources)
    restServer.start()
    
