from ha.HAClasses import *
from ha.fileInterface import *
from ha.solarInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    fileInterface = FileInterface("File", fileName=solarFileName, readOnly=True, event=stateChangeEvent)
    solarInterface = HASolarInterface("Solar", fileInterface)
    
    # Temperature
    resources.addRes(HASensor("inverterTemp", solarInterface, ("inverters", "avg", "Temp"), "Temperature", label="Inverter temp", type="tempC"))
    resources.addRes(HASensor("roofTemp", solarInterface, ("optimizers", "avg", "Temp"), "Temperature", label="Roof temp", type="tempC"))

    # Solar
    resources.addRes(HASensor("currentPower", solarInterface, ("inverters", "sum", "Pac"), "Solar", label="Current power", type="KW"))
    resources.addRes(HASensor("todaysEnergy", solarInterface, ("inverters", "sum", "Eday"), "Solar", label="Energy today", type="KWh"))
#    resources.addRes(HASensor("monthlyEnergy", solarInterface, ("stats", "", "Emonth"), "Solar", label="Energy this month", type="KWh"))
#    resources.addRes(HASensor("yearlyEnergy", solarInterface, ("stats", "", "Eyear"), "Solar", label="Energy this year", type="MWh"))
    resources.addRes(HASensor("lifetimeEnergy", solarInterface, ("inverters", "sum", "Etot"), "Solar", label="Lifetime energy", type="MWh"))

    # Start interfaces
    fileInterface.start()
    solarInterface.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Solar")
    restServer.start()
    
