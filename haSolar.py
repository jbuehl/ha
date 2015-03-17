from ha.HAClasses import *
from ha.fileInterface import *
from ha.solarInterface import *
from ha.restServer import *

if __name__ == "__main__":

    # Collections
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    resources.addRes(sensors)

    # Interfaces
    fileInterface = FileInterface("File", solarFileName, readOnly=True)
    solarInterface = HASolarInterface("Solar", fileInterface)
    
    # Temperature
    sensors.addRes(HASensor("inverterTemp", solarInterface, ("inverters", "avg", "Temp"), "Temperature", label="Inverter temp", type="tempC"))
    sensors.addRes(HASensor("roofTemp", solarInterface, ("optimizers", "avg", "Temp"), "Temperature", label="Roof temp", type="tempC"))

    # Solar
    sensors.addRes(HASensor("currentPower", solarInterface, ("inverters", "sum", "Pac"), "Solar", label="Current power", type="KW"))
    sensors.addRes(HASensor("todaysEnergy", solarInterface, ("inverters", "sum", "Eday"), "Solar", label="Energy today", type="KWh"))
#    sensors.addRes(HASensor("monthlyEnergy", solarInterface, ("stats", "", "Emonth"), "Solar", label="Energy this month", type="KWh"))
#    sensors.addRes(HASensor("yearlyEnergy", solarInterface, ("stats", "", "Eyear"), "Solar", label="Energy this year", type="MWh"))
    sensors.addRes(HASensor("lifetimeEnergy", solarInterface, ("inverters", "sum", "Etot"), "Solar", label="Lifetime energy", type="MWh"))

    # Start interfaces
    fileInterface.start()
    solarInterface.start()
    restServer = RestServer(resources)
    restServer.start()
    
