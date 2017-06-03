from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    gpioInterface = GPIOInterface("gpio", i2c1, addr=0x20, bank=1)

    # Sprinklers
    frontLawn = Control("frontLawn", gpioInterface, 4, group="Water", label="Front lawn valve") # yellow
    garden = Control("garden", gpioInterface, 5, group="Water", label="Garden valve") # red
    backLawn = Control("backLawn", gpioInterface, 6, group="Water", label="Back lawn valve") # green
    sideBeds = Control("sideBeds", gpioInterface, 3, group="Water", label="Side beds valve") # red
    backBeds = Control("backBeds", gpioInterface, 7, group="Water", label="Back beds valve") # blue

    # Sequences
    frontLawnSequence = Sequence("frontLawnSequence", [Cycle(frontLawn, 1200)], group="Water", label="Front lawn")
    gardenSequence = Sequence("gardenSequence", [Cycle(garden, 600)], group="Water", label="Garden")
    backLawnSequence = Sequence("backLawnSequence", [Cycle(backLawn, 1200)], group="Water", label="Back lawn")
    sideBedSequence = Sequence("sideBedSequence", [Cycle(sideBeds, 600)], group="Water", label="Side beds")
    backBedSequence = Sequence("backBedSequence", [Cycle(backBeds, 600)], group="Water", label="Back beds")

    # Schedules
    frontLawnTask = Task("frontLawnTask", SchedTime(hour=[21], minute=[00], weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), frontLawnSequence, 1, enabled=True)
    gardenTask = Task("gardenTask", SchedTime(hour=[21], minute=[20], month=[May, Jun, Jul, Aug, Sep]), gardenSequence, 1, enabled=True)
    backLawnTask = Task("backLawnTask", SchedTime(hour=[21], minute=[30], weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), backLawnSequence, 1, enabled=False)
    sideBedTask = Task("sideBedTask", SchedTime(hour=[21], minute=[50], weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), sideBedSequence, 1, enabled=True)
    backBedTask = Task("backBedTask", SchedTime(hour=[22], minute=[00], weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), backBedSequence, 1, enabled=False)
    schedule = Schedule("schedule", tasks=[frontLawnTask, gardenTask, backLawnTask, sideBedTask, backBedTask])

    # Resources
    resources = Collection("resources", resources=[frontLawn, garden, backLawn, sideBeds, backBeds, 
                                                   frontLawnSequence, gardenSequence, backLawnSequence, sideBedSequence, backBedSequence, 
                                                   frontLawnTask, gardenTask, backLawnTask, sideBedTask, backBedTask])
    restServer = RestServer(resources, event=stateChangeEvent, label="Sprinklers")

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer.start()

