from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    schedule = HASchedule("schedule")
    resources.addRes(schedule)

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpioInterface = GPIOInterface("GPIO", i2c1)
    
    # Doors
#    resources.addRes(HASensor("frontDoor", gpioInterface, 2, type="door", group="Doors", label="Front"))
#    resources.addRes(HASensor("familyRoomDoor", gpioInterface, 1, type="door", group="Doors", label="Family room"))
#    resources.addRes(HASensor("masterBedDoor", gpioInterface, 0, type="door", group="Doors", label="Master bedroom"))
#    resources.addRes(HASensor("garageBackDoor", gpioInterface, 3, type="door", group="Doors", label="Garage back"))
#    resources.addRes(HADoorSensor("Garage door", gpioInterface, 5, type="door", group="Doors"))
#    resources.addRes(HADoorSensor("Garage door house", gpioInterface, 4, type="door", group="Doors"))

    # Sprinklers
    resources.addRes(HAControl("frontLawn", gpioInterface, 3, group="Water", label="Front lawn")) # yellow
    resources.addRes(HAControl("backLawn", gpioInterface, 2, group="Water", label="Back lawn")) # green
    resources.addRes(HAControl("backBeds", gpioInterface, 1, group="Water", label="Back beds")) # blue
    resources.addRes(HAControl("sideBeds", gpioInterface, 0, group="Water", label="Side beds")) # red
    resources.addRes(HASequence("frontLawnSequence", [HACycle(resources["frontLawn"], 900)], group="Water", label="Front lawn 15 min"))
    resources.addRes(HASequence("gardenSequence", [HACycle(resources["backBeds"], 300)], group="Water", label="Garden 5 min"))
    resources.addRes(HASequence("backLawnSequence", [HACycle(resources["backLawn"], 600)], group="Water", label="Back lawn 10 min"))
    resources.addRes(HASequence("sideBedSequence", [HACycle(resources["sideBeds"], 600)], group="Water", label="Side beds 10 min"))

    # Temperature
#    resources.addRes(HASensor("insideTemp", i2c1, (0x48, 0x00), "Temperature", label="Inside temp", type="tempC"))

    # Schedules
    schedule.addTask(HATask("frontLawnTask", HASchedTime(hour=[22], minute=[00], weekday=[Sun, Mon, Tue, Wed, Thu, Fri, Sat]), resources["frontLawnSequence"], 1, enabled=True))
    schedule.addTask(HATask("gardenTask", HASchedTime(hour=[7], minute=[00], weekday=[Sun, Mon, Tue, Wed, Thu, Fri, Sat], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["gardenSequence"], 1, enabled=True))
    schedule.addTask(HATask("backLawnTask", HASchedTime(hour=[7], minute=[10], weekday=[Tue, Thu, Sat], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["backLawnSequence"], 1, enabled=True))
    schedule.addTask(HATask("sideBedTask", HASchedTime(hour=[7], minute=[30], weekday=[Sat], month=[May, Jun, Jul, Aug, Sep, Oct]), resources["sideBedSequence"], 1, enabled=True))

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer = RestServer(resources, event=stateChangeEvent)
    restServer.start()

