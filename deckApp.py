gpioPins = [18, 23, 24, 25, 22, 27, 17, 4]

from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.shadeInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":

    # Interfaces
    stateChangeEvent = threading.Event()
    gpioInterface = GPIOInterface("gpioInterface", output=gpioPins, event=stateChangeEvent)
    shadeInterface = ShadeInterface("shadeInterface", gpioInterface, gpioPins=gpioPins)

    # Controls
    shade1 = Control("shade1", shadeInterface, 0, type="shade", group="Shades", label="Shade 1")
    shade2 = Control("shade2", shadeInterface, 1, type="shade", group="Shades", label="Shade 2")
    shade3 = Control("shade3", shadeInterface, 2, type="shade", group="Shades", label="Shade 3")
    shade4 = Control("shade4", shadeInterface, 3, type="shade", group="Shades", label="Shade 4")
    allShades = ControlGroup("allShades", [shade1, shade2, shade3, shade4], type="shade", group="Shades", label="All shades")

    # Schedules
    shadesDown = Task("shadesDown", SchedTime(hour=[13], minute=[00], month=[Apr, May, Jun, Jul, Aug, Sep]), allShades, 1, group="Shades", enabled=True)
    shadesUpAprSep = Task("shadesUpAprSep", SchedTime(minute=-20, event="sunset", month=[Apr, Sep]), allShades, 0, group="Shades", enabled=True)
    shadesUpMayAug = Task("shadesUpMayAug", SchedTime(minute=-25, event="sunset", month=[May, Aug]), allShades, 0, group="Shades", enabled=True)
    shadesUpJunJul = Task("shadesUpJunJul", SchedTime(minute=-30, event="sunset", month=[Jun, Jul]), allShades, 0, group="Shades", enabled=True)
    schedule = Schedule("schedule", tasks=[shadesDown, shadesUpAprSep, shadesUpMayAug, shadesUpJunJul])

    # Resources
    resources = Collection("resources", resources=[shade1, shade2, shade3, shade4, allShades,
                                                   shadesDown, shadesUpAprSep, shadesUpMayAug, shadesUpJunJul])
    restServer = RestServer("deck", resources, event=stateChangeEvent, label="Deck")

    # Start interfaces
    gpioInterface.start()
    shadeInterface.start()
    schedule.start()
    restServer.start()
