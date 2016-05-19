import threading

from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.shadeInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    schedule = HASchedule("schedule")

    # Interfaces
    stateChangeEvent = threading.Event()
    gpioInterface = GPIOInterface("GPIO", event=stateChangeEvent)
    shadeInterface = ShadeInterface("Shades", gpioInterface)
    
    # Doors
    resources.addRes(HAControl("shade1", shadeInterface, 0, type="shade", group="Shades", label="Shade 1"))
    resources.addRes(HAControl("shade2", shadeInterface, 1, type="shade", group="Shades", label="Shade 2"))
    resources.addRes(HAControl("shade3", shadeInterface, 2, type="shade", group="Shades", label="Shade 3"))
    resources.addRes(HAControl("shade4", shadeInterface, 3, type="shade", group="Shades", label="Shade 4"))
    resources.addRes(HAScene("allShades", [resources["shade1"], 
                                           resources["shade2"],
                                           resources["shade3"],
                                           resources["shade4"]], type="shade", group="Shades", label="All shades"))

    # Schedules
    resources.addRes(schedule)
    schedule.addTask(HATask("shadesDown", HASchedTime(hour=[13], minute=[00], month=[Apr, May, Jun, Jul, Aug, Sep]), resources["allShades"], 1, enabled=True))
    schedule.addTask(HATask("shadesUpJunJul", HASchedTime(hour=[18], minute=[30], month=[Jun, Jul]), resources["allShades"], 0, enabled=True))
    schedule.addTask(HATask("shadesUpMayAug", HASchedTime(hour=[18], minute=[15], month=[May, Aug]), resources["allShades"], 0, enabled=True))
    schedule.addTask(HATask("shadesUpAprSep", HASchedTime(hour=[18], minute=[00], month=[Apr, Sep]), resources["allShades"], 0, enabled=True))

    # Start interfaces
    gpioInterface.start()
    shadeInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Shades")
    restServer.start()

