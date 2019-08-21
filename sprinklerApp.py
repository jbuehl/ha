tempSensorServices = []
tempSensorName = "outsideTemp"
initialMinTemp = 999
initialMaxTemp = 0

defaultConfig = {
    "startTime": 18*60,    # sprinkler start time in minutes past midnight
    "hotTemp": 100,        # temperature threshold to run extra
    "minTemp": initialMinTemp,
    "maxTemp": initialMaxTemp,
    "sideBedTime": 600,
    "frontLawnTime": 1200,
    "frontBedTime": 3600,
    "gardenTime": 120,
    "backLawnTime": 1200,
    "backBedTime": 600,
}

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
    stateInterface = FileInterface("stateInterface", fileName=stateDir+"sprinklers.state", event=stateChangeEvent, initialState=defaultConfig)
    stateInterface.start()

    # Sensors
    tempSensor = SensorGroup("tempSensor", [tempSensorName], resources=cacheResources)
    minTemp = MinSensor("minTemp", stateInterface, "minTemp", tempSensor, group=["Weather", "Sprinklers"], type="tempF", label="Min temp")
    maxTemp = MaxSensor("maxTemp", stateInterface, "maxTemp", tempSensor, group=["Weather", "Sprinklers"], type="tempF", label="Max temp")
    startTime = Control("startTime", stateInterface, "startTime", group="Sprinklers", type="timeControl", label="Sprinkler start time")
    hotTemp = Control("hotTemp", stateInterface, "hotTemp", group="Sprinklers", type="tempFControl", label="Hot temp threshold")

    # Sprinkler times
    sideBedTime = Control("sideBedTime", stateInterface, "sideBedTime", group="Sprinklers", label="Side beds time", type="timeControl")
    frontLawnTime = Control("frontLawnTime", stateInterface, "frontLawnTime", group="Sprinklers", label="Front lawn time", type="timeControl")
    frontBedTime = Control("frontBedTime", stateInterface, "frontBedTime", group="Sprinklers", label="Front beds time", type="timeControl")
    gardenTime = Control("gardenTime", stateInterface, "gardenTime", group="Sprinklers", label="Garden time", type="timeControl")
    backLawnTime = Control("backLawnTime", stateInterface, "backLawnTime", group="Sprinklers", label="Back lawn time", type="timeControl")
    backBedTime = Control("backBedTime", stateInterface, "backBedTime", group="Sprinklers", label="Back beds time", type="timeControl")

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
    frontBedSequence = Sequence("frontBedSequence", [Cycle(frontBeds, frontBedTime)], group="Sprinklers", label="Front beds")
    gardenSequence = Sequence("gardenSequence", [Cycle(garden, gardenTime)], group="Sprinklers", label="Garden")
    backLawnSequence = Sequence("backLawnSequence", [Cycle(backLawn, backLawnTime)], group="Sprinklers", label="Back lawn")
    backBedSequence = Sequence("backBedSequence", [Cycle(backBeds, backBedTime)], group="Sprinklers", label="Back beds")

    dailySequence = Sequence("dailySequence", [frontLawnSequence, backLawnSequence, backBedSequence, gardenSequence, sideBedSequence], group="Sprinklers", label="Daily sprinklers")
    weeklySequence = Sequence("weeklySequence", [frontBedSequence, dailySequence], group="Sprinklers", label="Weekly sprinklers")
    # run sprinklers if the day's max temp exceeds a threshold
    hotControl = DependentControl("hotControl", None, dailySequence, [(maxTemp, ">", hotTemp)], type="sequence", group="Sprinklers", label="Hot sprinklers")

    # Tasks
    resetMinTempTask = Task("resetMinTempTask", SchedTime(hour=0, minute=0), minTemp, initialMinTemp, enabled=True, group="Sprinklers")
    resetMaxTempTask = Task("resetMaxTempTask", SchedTime(hour=0, minute=0), maxTemp, initialMaxTemp, enabled=True, group="Sprinklers")
    startHour = startTime.getState() / 60
    dailyTask = Task("dailyTask", SchedTime(hour=startHour, minute=00, weekday=[Mon, Wed], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        dailySequence, 1, enabled=True, group="Sprinklers", label="Daily sprinkler task")
    weeklyTask = Task("weeklyTask", SchedTime(hour=startHour-1, minute=00, weekday=[Fri], month=[May, Jun, Jul, Aug, Sep, Oct]),
                        weeklySequence, 1, enabled=True, group="Sprinklers", label="Weekly sprinkler task")
    hotTask = Task("hotTask", SchedTime(hour=startHour, minute=00, weekday=[Tue, Thu, Sat, Sun], month=[May, Jun, Jul, Aug, Sep]),
                        hotControl, 1, enabled=True, group="Sprinklers", label="Hot sprinkler task")

    schedule = Schedule("schedule", tasks=[resetMinTempTask, resetMaxTempTask,
                                           dailyTask, weeklyTask, hotTask,
                                           ])

    # Resources
    resources = Collection("resources", resources=[startTime, hotTemp, minTemp, maxTemp,
                                                   frontLawn, frontBeds, garden, backLawn, sideBeds, backBeds,
                                                   frontLawnTime, frontBedTime, gardenTime, backLawnTime, sideBedTime, backBedTime,
                                                   frontLawnSequence, frontBedSequence, gardenSequence,
                                                   backLawnSequence, backBedSequence, sideBedSequence,
                                                   dailySequence, weeklySequence,
                                                   dailyTask, weeklyTask, hotTask,
                                                   resetMinTempTask, resetMaxTempTask,
                                                   ])
    restServer = RestServer("sprinklers", resources, event=stateChangeEvent, label="Sprinklers")

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer.start()
