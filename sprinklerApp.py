tempSensorServices = []
tempSensorName = "outsideTemp"
sideBedTimeDefault = 600
frontLawnTimeDefault = 1200
frontBedTimeDefault = 3600
gardenTimeDefault = 120
backLawnTimeDefault = 1200
backBedTimeDefault = 600

from ha import *
from ha.interfaces.fileInterface import *
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
    stateInterface = FileInterface("stateInterface", fileName=stateDir+"sprinklers.state", event=stateChangeEvent)

    # Sensors
    stateInterface.start()
    tempSensor = SensorGroup("tempSensor", [tempSensorName], resources=cacheResources)
    minTemp = MinSensor("minTemp", stateInterface, tempSensor, group="Weather", type="tempF", label="Min temp")
    maxTemp = MaxSensor("maxTemp", stateInterface, tempSensor, group="Weather", type="tempF", label="Max temp")

    # Sprinkler times
    sideBedTime = Control("sideBedTime", stateInterface, "sideBedTime", group="Sprinklers", label="Side beds time", type="timeControl")
    frontLawnTime = Control("frontLawnTime", stateInterface, "frontLawnTime", group="Sprinklers", label="Front lawn time", type="timeControl")
    frontBedTime = Control("frontBedTime", stateInterface, "frontBedTime", group="Sprinklers", label="Front beds time", type="timeControl")
    gardenTime = Control("gardenTime", stateInterface, "gardenTime", group="Sprinklers", label="Garden time", type="timeControl")
    backLawnTime = Control("backLawnTime", stateInterface, "backLawnTime", group="Sprinklers", label="Back lawn time", type="timeControl")
    backBedTime = Control("backBedTime", stateInterface, "backBedTime", group="Sprinklers", label="Back beds time", type="timeControl")
    if not sideBedTime.getState():
        sideBedTime.setState(sideBedTimeDefault)
    if not frontLawnTime.getState():
        frontLawnTime.setState(frontLawnTimeDefault)
    if not frontBedTime.getState():
        frontBedTime.setState(frontBedTimeDefault)
    if not gardenTime.getState():
        gardenTime.setState(gardenTimeDefault)
    if not backLawnTime.getState():
        backLawnTime.setState(backLawnTimeDefault)
    if not backBedTime.getState():
        backBedTime.setState(backBedTimeDefault)

    # Sprinkler valves
    sideBeds = Control("sideBeds", gpioInterface, 1, group="Sprinklers", label="Side beds valve") # red
    frontLawn = Control("frontLawn", gpioInterface, 2, group="Sprinklers", label="Front lawn valve") # yellow
    frontBeds = Control("frontBeds", gpioInterface, 3, group="Sprinklers", label="Front beds valve") # green
    garden = Control("garden", gpioInterface, 5, group="Sprinklers", label="Garden valve") # red
    backLawn = Control("backLawn", gpioInterface, 6, group="Sprinklers", label="Back lawn valve") # green
    backBeds = Control("backBeds", gpioInterface, 7, group="Sprinklers", label="Back beds valve") # blue

    # Sequences
    sideBedSequence = Sequence("sideBedSequence", [Cycle(sideBeds, sideBedTime)], group="Sprinklers", label="Side beds")
    frontLawnSequence = Sequence("frontLawnSequence", [Cycle(frontLawn, frontLawnTime)], group="Sprinklers", label="Front lawn")
    frontLawnHotSequence = DependentControl("frontLawnHotSequence", None, frontLawnSequence, [(maxTemp, ">", 95)])
    frontBedSequence = Sequence("frontBedSequence", [Cycle(frontBeds, frontBedTime)], group="Sprinklers", label="Front beds")
    gardenSequence = Sequence("gardenSequence", [Cycle(garden, gardenTime)], group="Sprinklers", label="Garden")
    backLawnSequence = Sequence("backLawnSequence", [Cycle(backLawn, backLawnTime)], group="Sprinklers", label="Back lawn")
    backLawnHotSequence = DependentControl("backLawnHotSequence", None, backLawnSequence, [(maxTemp, ">", 95)])
    backBedSequence = Sequence("backBedSequence", [Cycle(backBeds, backBedTime)], group="Sprinklers", label="Back beds")
    backBedHotSequence = DependentControl("backBedHotSequence", None, backBedSequence, [(tempSensor, ">", 90)])
    backBedHotterSequence = DependentControl("backBedHotterSequence", None, backBedSequence, [(maxTemp, ">", 100)])

    # Schedules
    resetMinTempTask = Task("resetMinTempTask", SchedTime(hour=0, minute=0), minTemp, 999, enabled=True)
    resetMaxTempTask = Task("resetMaxTempTask", SchedTime(hour=0, minute=0), maxTemp, 0, enabled=True)

    backBedHotTask = Task("backBedHotTask", SchedTime(hour=14, minute=00, month=[Jun, Jul, Aug, Sep]), backBedHotSequence, 1, enabled=True)
    backBedHotterTask = Task("backBedHotterTask", SchedTime(hour=16, minute=00, month=[Jun, Jul, Aug, Sep]), backBedHotterSequence, 1, enabled=True)

    scheduleHour = 18
    frontLawnTask = Task("frontLawnTask", SchedTime(hour=scheduleHour, minute=00, weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        frontLawnSequence, 1, enabled=True)
    frontLawnHotTask = Task("frontLawnHotTask", SchedTime(hour=scheduleHour, minute=00, weekday=[Tue, Thu, Sat, Sun], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        frontLawnHotSequence, 1, enabled=True)
    frontBedTask = Task("frontBedTask", SchedTime(hour=scheduleHour-1, minute=00, weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        frontBedSequence, 1, enabled=True)
    backLawnTask = Task("backLawnTask", SchedTime(hour=scheduleHour, minute=20, weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        backLawnSequence, 1, enabled=True)
    backLawnHotTask = Task("backLawnHotTask", SchedTime(hour=scheduleHour, minute=20, weekday=[Tue, Thu, Sat, Sun], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        backLawnHotSequence, 1, enabled=True)
    gardenTask = Task("gardenTask", SchedTime(hour=scheduleHour, minute=40, weekday=[Tue, Thu, Sat, Sun], month=[May, Jun, Jul, Aug, Sep]),
                        gardenSequence, 1, enabled=True)
    backBedTask = Task("backBedTask", SchedTime(hour=scheduleHour, minute=50, weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        backBedSequence, 1, enabled=True)
    sideBedTask = Task("sideBedTask", SchedTime(hour=scheduleHour+1, minute=00, weekday=[Mon, Wed, Fri], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        sideBedSequence, 1, enabled=True)

    schedule = Schedule("schedule", tasks=[resetMinTempTask, resetMaxTempTask,
                                           frontLawnTask, frontLawnHotTask, frontBedTask, gardenTask,
                                           backLawnTask, backLawnHotTask,
                                           sideBedTask, backBedTask, backBedHotTask, backBedHotterTask])

    # Resources
    resources = Collection("resources", resources=[minTemp, maxTemp,
                                                   frontLawn, frontBeds, garden, backLawn, sideBeds, backBeds,
                                                   frontLawnTime, frontBedTime, gardenTime, backLawnTime, sideBedTime, backBedTime,
                                                   frontLawnSequence, frontLawnHotSequence, frontBedSequence, gardenSequence,
                                                   backLawnSequence, backLawnHotSequence, sideBedSequence, backBedSequence,
                                                   backBedHotSequence, backBedHotterSequence,
                                                   resetMinTempTask, resetMaxTempTask,
                                                   backBedHotTask, backBedHotterTask,
                                                   frontLawnTask, frontLawnHotTask, frontBedTask,
                                                   backLawnTask, backLawnHotTask,
                                                   gardenTask, backBedTask, sideBedTask])
    restServer = RestServer("sprinklers", resources, event=stateChangeEvent, label="Sprinklers")

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer.start()
