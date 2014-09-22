from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.restServer import *
from ha.logging import *

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    nullInterface = HAInterface("Null", HAInterface("None"))
    i2c1 = HAI2CInterface("I2C1", 1)
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
#    sensors.addRes(HAControl("Front lawn", gpioInterface, GPIOAddr(0,1,0,1), "Sprinklers"))
#    sensors.addRes(HAControl("Parkway", gpioInterface, GPIOAddr(0,1,1,1), "Sprinklers"))
    sensors.addRes(HAControl("frontLawn", gpioInterface, GPIOAddr(0,0,3,1), group="Sprinklers", label="Front lawn")) # red
    sensors.addRes(HAControl("backLawn", gpioInterface, GPIOAddr(0,0,2,1), group="Sprinklers", label="Back lawn")) # blue
    sensors.addRes(HAControl("backBeds", gpioInterface, GPIOAddr(0,0,1,1), group="Sprinklers", label="Back beds")) # green
    sensors.addRes(HAControl("sideBeds", gpioInterface, GPIOAddr(0,0,0,1), group="Sprinklers", label="Side beds")) # yellow
    sensors.addRes(HASequence("gardenSequence", [HACycle(sensors["backBeds"], 600)], group="Sprinklers", label="Garden 10 min"))
    sensors.addRes(HASequence("backLawnSequence", [HACycle(sensors["backLawn"], 1200)], group="Sprinklers", label="Back lawn 20 min"))
    sensors.addRes(HASequence("sideBedSequence", [HACycle(sensors["sideBeds"], 900)], group="Sprinklers", label="Side beds 15 min"))

    # Temperature
#    sensors.addRes(HASensor("insideTemp", i2c1, (0x48, 0x00), "Temperature", label="Inside temp", type="tempC"))

    # Schedules
    schedule.addTask(HATask("gardenTask", HASchedTime(hour=[7], minute=[00], weekday=[Sun, Mon, Tue, Wed, Thu, Fri, Sat]), sensors["gardenSequence"], 1, enabled=True))
    schedule.addTask(HATask("backLawnTask", HASchedTime(hour=[7], minute=[10], weekday=[Tue, Thu, Sat]), sensors["backLawnSequence"], 1, enabled=True))
    schedule.addTask(HATask("sideBedTask", HASchedTime(hour=[7], minute=[30], weekday=[Sat]), sensors["sideBedSequence"], 1, enabled=True))

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

