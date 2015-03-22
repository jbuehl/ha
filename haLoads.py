from ha.HAClasses import *
from ha.fileInterface import *
from ha.loadInterface import *
from ha.restServer import *

if __name__ == "__main__":

    # Collections
    resources = HACollection("resources")

    # Interfaces
    fileInterface = FileInterface("File", loadFileName, readOnly=True)
    loadInterface = LoadInterface("Loads", fileInterface)

    # Loads
    resources.addRes(HASensor("lightsLoad", loadInterface, "Lights", group="Power", label="Lights", type="KVA"))
    resources.addRes(HASensor("plugsLoad", loadInterface, "Plugs", group="Power", label="Plugs", type="KVA"))
    resources.addRes(HASensor("appl1Load", loadInterface, "Appl1", group="Power", label="Appliances 1", type="KVA"))
    resources.addRes(HASensor("appl2Load", loadInterface, "Appl2", group="Power", label="Appliances 2", type="KVA"))
    resources.addRes(HASensor("cookingLoad", loadInterface, "Cooking", group="Power", label="Stove & oven", type="KVA"))
    resources.addRes(HASensor("acLoad", loadInterface, "Ac", group="Power", label="Air conditioners", type="KVA"))
    resources.addRes(HASensor("poolLoad", loadInterface, "Pool", group="Power", label="Pool equipment", type="KVA"))
    resources.addRes(HASensor("backLoad", loadInterface, "Back", group="Power", label="Back house", type="KVA"))

    # Start interfaces
    fileInterface.start()
    loadInterface.start()
    restServer = RestServer(resources)
    restServer.start()
    
