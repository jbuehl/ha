from ha.HAClasses import *
from ha.fileInterface import *
from ha.loadInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    fileInterface = FileInterface("File", fileName=loadFileName, readOnly=True, event=stateChangeEvent)
    loadInterface = LoadInterface("Loads", fileInterface)

    # Loads
    lightsLoad = HASensor("lightsLoad", loadInterface, "Lights", group="Power", label="Lights", type="KVA")
    plugsLoad = HASensor("plugsLoad", loadInterface, "Plugs", group="Power", label="Plugs", type="KVA")
    appl1Load = HASensor("appl1Load", loadInterface, "Appl1", group="Power", label="Appliances 1", type="KVA")
    appl2Load = HASensor("appl2Load", loadInterface, "Appl2", group="Power", label="Appliances 2", type="KVA")
    cookingLoad = HASensor("cookingLoad", loadInterface, "Cooking", group="Power", label="Stove & oven", type="KVA")
    acLoad = HASensor("acLoad", loadInterface, "Ac", group="Power", label="Air conditioners", type="KVA")
    poolLoad = HASensor("poolLoad", loadInterface, "Pool", group="Power", label="Pool equipment", type="KVA")
    backLoad = HASensor("backLoad", loadInterface, "Back", group="Power", label="Back house", type="KVA")
    resources.addRes(HASensor("lightsLoad", loadInterface, "Lights", group="Power", label="Lights", type="KVA"))
    resources.addRes(plugsLoad)
    resources.addRes(appl1Load)
    resources.addRes(appl2Load)
    resources.addRes(cookingLoad)
    resources.addRes(acLoad)
    resources.addRes(poolLoad)
    resources.addRes(backLoad)
    currentLoad = CalcSensor("currentLoad", [lightsLoad, plugsLoad, appl1Load, appl2Load, cookingLoad, acLoad, poolLoad, backLoad], "sum", group="Power", label="Current load", type="KVA")
    resources.addRes(currentLoad)

    # Start interfaces
    fileInterface.start()
    loadInterface.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Loads")
    restServer.start()
    
