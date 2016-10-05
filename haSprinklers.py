from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    schedule = HASchedule("schedule")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpioInterface = GPIOInterface("GPIO", i2c1, addr=0x20, bank=1)

    # Sprinklers
    resources.addRes(HAControl("frontLawn", gpioInterface, 4, group="Water", label="Front lawn valve")) # yellow
    resources.addRes(HAControl("garden", gpioInterface, 5, group="Water", label="Garden valve")) # red
    resources.addRes(HAControl("backLawn", gpioInterface, 6, group="Water", label="Back lawn valve")) # green
    resources.addRes(HAControl("backBeds", gpioInterface, 7, group="Water", label="Back beds valve")) # blue
    resources.addRes(HAControl("sideBeds", gpioInterface, 3, group="Water", label="Side beds valve")) # red

    # Sequences
    resources.addRes(HASequence("frontLawnSequence", [HACycle(resources["frontLawn"], 1200)], group="Water", label="Front lawn"))
    resources.addRes(HASequence("gardenSequence", [HACycle(resources["garden"], 600)], group="Water", label="Garden"))
    resources.addRes(HASequence("backLawnSequence", [HACycle(resources["backLawn"], 1200)], group="Water", label="Back lawn"))
    resources.addRes(HASequence("sideBedSequence", [HACycle(resources["sideBeds"], 600)], group="Water", label="Side beds"))
    resources.addRes(HASequence("backBedSequence", [HACycle(resources["backBeds"], 600)], group="Water", label="Back beds"))

    # Schedules
    resources.addRes(schedule)
    schedule.addTask(HATask("frontLawnTask", HASchedTime(hour=[21], minute=[00], weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["frontLawnSequence"], 1, enabled=True))
    schedule.addTask(HATask("gardenTask", HASchedTime(hour=[21], minute=[20], month=[May, Jun, Jul, Aug, Sep]), resources["gardenSequence"], 1, enabled=True))
    schedule.addTask(HATask("backLawnTask", HASchedTime(hour=[21], minute=[30], weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["backLawnSequence"], 1, enabled=True))
    schedule.addTask(HATask("sideBedTask", HASchedTime(hour=[21], minute=[50], weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["sideBedSequence"], 1, enabled=True))
    schedule.addTask(HATask("backBedTask", HASchedTime(hour=[22], minute=[00], weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["backBedSequence"], 1, enabled=True))

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Sprinklers")
    restServer.start()

