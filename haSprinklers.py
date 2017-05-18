from ha import *
from ha.gpioInterface import *
from ha.i2cInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = Collection("resources")
    schedule = Schedule("schedule")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpioInterface = GPIOInterface("GPIO", i2c1, addr=0x20, bank=1)

    # Sprinklers
    resources.addRes(Control("frontLawn", gpioInterface, 4, group="Water", label="Front lawn valve")) # yellow
    resources.addRes(Control("garden", gpioInterface, 5, group="Water", label="Garden valve")) # red
    resources.addRes(Control("backLawn", gpioInterface, 6, group="Water", label="Back lawn valve")) # green
    resources.addRes(Control("backBeds", gpioInterface, 7, group="Water", label="Back beds valve")) # blue
    resources.addRes(Control("sideBeds", gpioInterface, 3, group="Water", label="Side beds valve")) # red

    # Sequences
    resources.addRes(Sequence("frontLawnSequence", [Cycle(resources["frontLawn"], 1200)], group="Water", label="Front lawn"))
    resources.addRes(Sequence("gardenSequence", [Cycle(resources["garden"], 600)], group="Water", label="Garden"))
    resources.addRes(Sequence("backLawnSequence", [Cycle(resources["backLawn"], 1200)], group="Water", label="Back lawn"))
    resources.addRes(Sequence("sideBedSequence", [Cycle(resources["sideBeds"], 600)], group="Water", label="Side beds"))
    resources.addRes(Sequence("backBedSequence", [Cycle(resources["backBeds"], 600)], group="Water", label="Back beds"))

    # Schedules
    resources.addRes(schedule)
    schedule.addTask(Task("frontLawnTask", SchedTime(hour=[21], minute=[00], weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["frontLawnSequence"], 1, enabled=True))
    schedule.addTask(Task("gardenTask", SchedTime(hour=[21], minute=[20], month=[May, Jun, Jul, Aug, Sep]), resources["gardenSequence"], 1, enabled=False))
    schedule.addTask(Task("backLawnTask", SchedTime(hour=[21], minute=[30], weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["backLawnSequence"], 1, enabled=False))
    schedule.addTask(Task("sideBedTask", SchedTime(hour=[21], minute=[50], weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["sideBedSequence"], 1, enabled=True))
    schedule.addTask(Task("backBedTask", SchedTime(hour=[22], minute=[00], weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["backBedSequence"], 1, enabled=False))

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Sprinklers")
    restServer.start()

