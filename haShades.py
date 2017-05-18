import threading

from ha import *
from ha.gpioInterface import *
from ha.shadeInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = Collection("resources")
    schedule = Schedule("schedule")

    # Interfaces
    stateChangeEvent = threading.Event()
    gpioInterface = GPIOInterface("GPIO", event=stateChangeEvent)
    shadeInterface = ShadeInterface("Shades", gpioInterface)
    
    # Doors
    resources.addRes(Control("shade1", shadeInterface, 0, type="shade", group="Shades", label="Shade 1"))
    resources.addRes(Control("shade2", shadeInterface, 1, type="shade", group="Shades", label="Shade 2"))
    resources.addRes(Control("shade3", shadeInterface, 2, type="shade", group="Shades", label="Shade 3"))
    resources.addRes(Control("shade4", shadeInterface, 3, type="shade", group="Shades", label="Shade 4"))
    resources.addRes(ControlGroup("allShades", [resources["shade1"], 
                                           resources["shade2"],
                                           resources["shade3"],
                                           resources["shade4"]], type="shade", group="Shades", label="All shades"))

    # Schedules
    resources.addRes(schedule)
    schedule.addTask(Task("shadesDown", SchedTime(hour=[13], minute=[00], month=[Apr, May, Jun, Jul, Aug, Sep]), resources["allShades"], 1, enabled=True))
    schedule.addTask(Task("shadesUp", SchedTime(minute=-30, event="sunset", month=[Apr, May, Jun, Jul, Aug, Sep]), resources["allShades"], 0, enabled=True))
#    schedule.addTask(Task("shadesUpJunJul", SchedTime(hour=[19], minute=[15], month=[Jun, Jul]), resources["allShades"], 0, enabled=True))
#    schedule.addTask(Task("shadesUpMayAug", SchedTime(hour=[19], minute=[00], month=[May, Aug]), resources["allShades"], 0, enabled=True))
#    schedule.addTask(Task("shadesUpAprSep", SchedTime(hour=[18], minute=[45], month=[Apr, Sep]), resources["allShades"], 0, enabled=True))

    # Start interfaces
    gpioInterface.start()
    shadeInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Shades")
    restServer.start()

