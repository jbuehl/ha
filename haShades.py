import threading

from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.MCP9803Interface import *
from ha.tempInterface import *
from ha.shadeInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    schedule = HASchedule("schedule")
    resources.addRes(schedule)

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    mcp9803 = MCP9803Interface("MCP9803", i2c1)
    temp = TempInterface("Temp", mcp9803, sample=10)
    gpioInterface = GPIOInterface("GPIO", event=stateChangeEvent)
    shadeInterface = ShadeInterface("Shades", gpioInterface)
    
    # Doors
    resources.addRes(HAControl("shade1", shadeInterface, 0, type="shade", group="Doors", label="Shade 1"))
    resources.addRes(HAControl("shade2", shadeInterface, 1, type="shade", group="Doors", label="Shade 2"))
    resources.addRes(HAControl("shade3", shadeInterface, 2, type="shade", group="Doors", label="Shade 3"))
    resources.addRes(HAControl("shade4", shadeInterface, 3, type="shade", group="Doors", label="Shade 4"))
    resources.addRes(HAScene("allShades", [resources["shade1"], 
                                      resources["shade2"],
                                      resources["shade3"],
                                      resources["shade4"]], type="shade", group="Doors", label="All shades"))

    # Temperature
    resources.addRes(HASensor("deckTemp", temp, 0x49, group="Temperature", label="Deck temp", type="tempF"))
    
    # Schedules
    schedule.addTask(HATask("Shades down", HASchedTime(hour=[13], minute=[00], month=[Apr, May, Jun, Jul, Aug, Sep]), resources["allShades"], 1, enabled=True))
    schedule.addTask(HATask("Shades up Jun, Jul", HASchedTime(hour=[18], minute=[30], month=[Jun, Jul]), resources["allShades"], 0, enabled=True))
    schedule.addTask(HATask("Shades up May, Aug", HASchedTime(hour=[18], minute=[15], month=[May, Aug]), resources["allShades"], 0, enabled=True))
    schedule.addTask(HATask("Shades up Apr, Sep", HASchedTime(hour=[18], minute=[00], month=[Apr, Sep]), resources["allShades"], 0, enabled=True))

    # Start interfaces
    gpioInterface.start()
    shadeInterface.start()
    temp.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent)
    restServer.start()

