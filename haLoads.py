from ha import *
from ha.interfaces.fileInterface import *
from ha.interfaces.loadInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = Collection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    fileInterface = FileInterface("File", fileName=loadFileName, readOnly=True, event=stateChangeEvent)
    loadInterface = LoadInterface("Loads", fileInterface)

    # Loads
    lightsLoad = Sensor("lightsLoad", loadInterface, "Lights", group="Power", label="Lights", type="KVA")
    plugsLoad = Sensor("plugsLoad", loadInterface, "Plugs", group="Power", label="Plugs", type="KVA")
    appl1Load = Sensor("appl1Load", loadInterface, "Appl1", group="Power", label="Appliances 1", type="KVA")
    appl2Load = Sensor("appl2Load", loadInterface, "Appl2", group="Power", label="Appliances 2", type="KVA")
    cookingLoad = Sensor("cookingLoad", loadInterface, "Cooking", group="Power", label="Stove & oven", type="KVA")
    acLoad = Sensor("acLoad", loadInterface, "Ac", group="Power", label="Air conditioners", type="KVA")
    poolLoad = Sensor("poolLoad", loadInterface, "Pool", group="Power", label="Pool equipment", type="KVA")
    backLoad = Sensor("backLoad", loadInterface, "Back", group="Power", label="Back house", type="KVA")
    resources.addRes(Sensor("lightsLoad", loadInterface, "Lights", group="Power", label="Lights", type="KVA"))
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
    
