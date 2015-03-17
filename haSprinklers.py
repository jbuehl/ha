from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.restServer import *

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    nullInterface = HAInterface("Null", HAInterface("None"))
    i2c1 = I2CInterface("I2C1", 1)
    gpioInterface = GPIOInterface("GPIO", i2c1)
    
    sensors.addRes(HAControl("Null", nullInterface, None))
    
    # Doors
#    sensors.addRes(HASensor("frontDoor", gpioInterface, GPIOAddr(0,0,2,1), type="door", group="Doors", label="Front"))
#    sensors.addRes(HASensor("familyRoomDoor", gpioInterface, GPIOAddr(0,0,1,1), type="door", group="Doors", label="Family room"))
#    sensors.addRes(HASensor("masterBedDoor", gpioInterface, GPIOAddr(0,0,0,1), type="door", group="Doors", label="Master bedroom"))
#    sensors.addRes(HASensor("garageBackDoor", gpioInterface, GPIOAddr(0,0,3,1), type="door", group="Doors", label="Garage back"))
#    sensors.addRes(HADoorSensor("Garage door", gpioInterface, GPIOAddr(0,0,5,1), type="door", group="Doors"))
#    sensors.addRes(HADoorSensor("Garage door house", gpioInterface, GPIOAddr(0,0,4,1), type="door", group="Doors"))

    # Sprinklers
    sensors.addRes(HAControl("frontLawn", gpioInterface, GPIOAddr(0,0,3,1), group="Water", label="Front lawn")) # yellow
    sensors.addRes(HAControl("backLawn", gpioInterface, GPIOAddr(0,0,2,1), group="Water", label="Back lawn")) # green
    sensors.addRes(HAControl("backBeds", gpioInterface, GPIOAddr(0,0,1,1), group="Water", label="Back beds")) # blue
    sensors.addRes(HAControl("sideBeds", gpioInterface, GPIOAddr(0,0,0,1), group="Water", label="Side beds")) # red
    sensors.addRes(HASequence("frontLawnSequence", [HACycle(sensors["frontLawn"], 600)], group="Water", label="Front lawn 10 min"))
    sensors.addRes(HASequence("gardenSequence", [HACycle(sensors["backBeds"], 300)], group="Water", label="Garden 5 min"))
    sensors.addRes(HASequence("backLawnSequence", [HACycle(sensors["backLawn"], 600)], group="Water", label="Back lawn 10 min"))
    sensors.addRes(HASequence("sideBedSequence", [HACycle(sensors["sideBeds"], 600)], group="Water", label="Side beds 10 min"))

    # Temperature
#    sensors.addRes(HASensor("insideTemp", i2c1, (0x48, 0x00), "Temperature", label="Inside temp", type="tempC"))

    # Schedules
    schedule.addTask(HATask("frontLawnTask", HASchedTime(hour=[7], minute=[00], weekday=[Sun, Mon, Tue, Wed, Thu, Fri, Sat]), sensors["frontLawnSequence"], 1, enabled=True))
    schedule.addTask(HATask("gardenTask", HASchedTime(hour=[7], minute=[00], weekday=[Sun, Mon, Tue, Wed, Thu, Fri, Sat], month=[May, Jun, Jul, Aug, Sep, Oct]), sensors["gardenSequence"], 1, enabled=True))
    schedule.addTask(HATask("backLawnTask", HASchedTime(hour=[7], minute=[10], weekday=[Tue, Thu, Sat], month=[May, Jun, Jul, Aug, Sep, Oct]), sensors["backLawnSequence"], 1, enabled=True))
    schedule.addTask(HATask("sideBedTask", HASchedTime(hour=[7], minute=[30], weekday=[Sat], month=[May, Jun, Jul, Aug, Sep, Oct]), sensors["sideBedSequence"], 1, enabled=True))

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

