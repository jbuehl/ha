from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
#from ha.applianceInterface import *
from ha.restServer import *

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
#    gpioInterface = GPIOInterface("GPIO")
#    applianceInterface = ApplianceInterface("garage", gpioInterface)
    i2c1 = I2CInterface("I2C1", 1)
    gpioInterface = GPIOInterface("GPIO", i2c1, addr=0x20, config=[(0x00, 0x00), (0x01, 0xff), (0x03, 0xff), (0x0d, 0xff)])
    
    # Lights
    sensors.addRes(HAControl("frontLights", gpioInterface, GPIOAddr(0,0,0), type="light", group="Lights", label="Front lights"))
    sensors.addRes(HAControl("garageBackDoorLight", gpioInterface, GPIOAddr(0,0,1), type="light", group="Lights", label="Garage back door light"))
#    sensors.addRes(HASensor("garageBackDoorSwitch", applianceInterface, 1, type="light", group="Lights", label="Garage back door switch"))
    sensors.addRes(HAScene("garageLights", [sensors["frontLights"],
                                             sensors["garageBackDoorLight"]], group="Lights", label="Garage"))

    # Schedules
    schedule.addTask(HATask("Garage lights on sunset", HASchedTime(event="sunset"), sensors["garageLights"], 1))
    schedule.addTask(HATask("Garage lights off midnight", HASchedTime(hour=[23,0], minute=[00]), sensors["garageLights"], 0))
    schedule.addTask(HATask("Garage lights off sunrise", HASchedTime(event="sunrise"), sensors["garageLights"], 0))

    # Start interfaces
#    applianceInterface.start()
    gpioInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

