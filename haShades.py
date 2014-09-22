from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.shadeInterface import *
from ha.restServer import *
from ha.logging import *

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    gpioInterface = GPIOInterface("GPIO")
    shadeInterface = ShadeInterface("Shades", gpioInterface)
    
    # Doors
    sensors.addRes(HAControl("shade1", shadeInterface, 0, type="shade", group="Doors", label="Shade 1"))
    sensors.addRes(HAControl("shade2", shadeInterface, 1, type="shade", group="Doors", label="Shade 2"))
    sensors.addRes(HAControl("shade3", shadeInterface, 2, type="shade", group="Doors", label="Shade 3"))
    sensors.addRes(HAControl("shade4", shadeInterface, 3, type="shade", group="Doors", label="Shade 4"))
    sensors.addRes(HAScene("allShades", [sensors["shade1"], 
                                      sensors["shade2"],
                                      sensors["shade3"],
                                      sensors["shade4"]], [[0,1], [0,1], [0,1], [0,1]], type="shade", group="Doors", label="All shades"))

    # Schedules
    schedule.addTask(HATask("Shades down", HASchedTime(hour=[13], minute=[00], month=[May, Jun, Jul, Aug, Sep]), sensors["allShades"], 1, enabled=True))
    schedule.addTask(HATask("Shades up Jun, Jul", HASchedTime(hour=[18], minute=[30], month=[Jun, Jul]), sensors["allShades"], 0, enabled=True))
    schedule.addTask(HATask("Shades up May, Aug", HASchedTime(hour=[18], minute=[15], month=[May, Aug]), sensors["allShades"], 0, enabled=True))
    schedule.addTask(HATask("Shades up Sep", HASchedTime(hour=[18], minute=[00], month=[Sep]), sensors["allShades"], 0, enabled=True))

    # Start interfaces
    shadeInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

