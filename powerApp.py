from ha import *
from ha.interfaces.fileInterface import *
# from ha.interfaces.loadInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    fileInterface = FileInterface("fileInterface", fileName=loadFileName, readOnly=True, event=stateChangeEvent)

    # Loads
    lightsLoad = Sensor("loads.lights.power", fileInterface, "Lights", group=["Power", "Loads"], label="Lights", type="KVA")
    plugsLoad = Sensor("loads.plugs.power", fileInterface, "Plugs", group=["Power", "Loads"], label="Plugs", type="KVA")
    appl1Load = Sensor("loads.appliance1.power", fileInterface, "Appl1", group=["Power", "Loads"], label="Appliances 1", type="KVA")
    appl2Load = Sensor("loads.appliance2.power", fileInterface, "Appl2", group=["Power", "Loads"], label="Appliances 2", type="KVA")
    cookingLoad = Sensor("loads.cooking.power", fileInterface, "Cooking", group=["Power", "Loads"], label="Stove & oven", type="KVA")
    acLoad = Sensor("loads.ac.power", fileInterface, "Ac", group=["Power", "Loads"], label="Air conditioners", type="KVA")
    poolLoad = Sensor("loads.pool.power", fileInterface, "Pool", group=["Power", "Loads"], label="Pool equipment", type="KVA")
    backLoad = Sensor("loads.backhouse.power", fileInterface, "Back", group=["Power", "Loads"], label="Back house", type="KVA")
    currentLoad = Sensor("loads.stats.power", fileInterface, "Total", group=["Power", "Loads"], label="Current load", type="KVA")
    dailyLoad = Sensor("loads.stats.dailyEnergy", fileInterface, "Daily", group=["Power", "Loads"], label="Daily load", type="KVAh")

    # Resources
    resources = Collection("resources", resources=[lightsLoad, plugsLoad, appl1Load, appl2Load, cookingLoad, acLoad, poolLoad, backLoad,
                                                   currentLoad, dailyLoad])
    restServer = RestServer("power", resources=resources, event=stateChangeEvent, label="Loads")

    # Start interfaces
    fileInterface.start()
    # loadInterface.start()
    restServer.start()
