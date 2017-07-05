tempSensorServices = []
tempSensorName = "outsideTemp"

from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    cacheResources = Collection("cacheResources")
    restCache = RestProxy("restProxy", cacheResources, watch=tempSensorServices, event=stateChangeEvent)
    restCache.start()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    gpioInterface = GPIOInterface("gpio", i2c1, addr=0x20, bank=1)

    # Sensors
    tempSensor = SensorGroup("tempSensor", [tempSensorName], resources=cacheResources)

    # Sprinklers
    frontLawn = Control("frontLawn", gpioInterface, 4, group="Sprinklers", label="Front lawn valve") # yellow
    garden = Control("garden", gpioInterface, 5, group="Sprinklers", label="Garden valve") # red
    backLawn = Control("backLawn", gpioInterface, 6, group="Sprinklers", label="Back lawn valve") # green
    sideBeds = Control("sideBeds", gpioInterface, 3, group="Sprinklers", label="Side beds valve") # red
    backBeds = Control("backBeds", gpioInterface, 7, group="Sprinklers", label="Back beds valve") # blue

    # Sequences
    frontLawnSequence = Sequence("frontLawnSequence", [Cycle(frontLawn, 1200)], group="Sprinklers", label="Front lawn")
    gardenSequence = Sequence("gardenSequence", [Cycle(garden, 600)], group="Sprinklers", label="Garden")
    backLawnSequence = Sequence("backLawnSequence", [Cycle(backLawn, 1200)], group="Sprinklers", label="Back lawn")
    sideBedSequence = Sequence("sideBedSequence", [Cycle(sideBeds, 600)], group="Sprinklers", label="Side beds")
    backBedSequence = Sequence("backBedSequence", [Cycle(backBeds, 300)], group="Sprinklers", label="Back beds")
    backBedSequence90 = DependentControl("backBedSequence90", None, backBedSequence, [(tempSensor, ">", 90)])
    backBedSequence100 = DependentControl("backBedSequence100", None, backBedSequence, [(tempSensor, ">", 100)])

    # Schedules
    frontLawnTask = Task("frontLawnTask", SchedTime(hour=21, minute=00, weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), frontLawnSequence, 1, enabled=True)
    gardenTask = Task("gardenTask", SchedTime(hour=21, minute=20, month=[May, Jun, Jul, Aug, Sep]), gardenSequence, 1, enabled=True)
    backLawnTask = Task("backLawnTask", SchedTime(hour=21, minute=30, weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), backLawnSequence, 1, enabled=False)
    sideBedTask = Task("sideBedTask", SchedTime(hour=21, minute=50, weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]), sideBedSequence, 1, enabled=True)
    backBedTask = Task("backBedTask", SchedTime(hour=22, minute=00, month=[May, Jun, Jul, Aug, Sep, Oct]), backBedSequence, 1, enabled=True)
    backBed90Task = Task("backBed90Task", SchedTime(hour=14, minute=00, month=[Jun, Jul, Aug, Sep]), backBedSequence90, 1, enabled=True)
    backBed100Task = Task("backBed100Task", SchedTime(hour=16, minute=00, month=[Jun, Jul, Aug, Sep]), backBedSequence100, 1, enabled=True)
    schedule = Schedule("schedule", tasks=[frontLawnTask, gardenTask, backLawnTask, sideBedTask, backBedTask, backBed90Task, backBed100Task])

    # Resources
    resources = Collection("resources", resources=[frontLawn, garden, backLawn, sideBeds, backBeds, 
                                                   frontLawnSequence, gardenSequence, backLawnSequence, sideBedSequence, backBedSequence, 
                                                   backBedSequence90, backBedSequence100, 
                                                   frontLawnTask, gardenTask, backLawnTask, sideBedTask, backBedTask,
                                                   backBed90Task, backBed100Task])
    restServer = RestServer(resources, event=stateChangeEvent, label="Sprinklers")

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer.start()

