from ha.HAClasses import *
from ha.I2CInterface import *
from ha.GPIOInterface import *
#from ha.applianceInterface import *
from ha.restServer import *

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    i2c1 = I2CInterface("I2C1", 1)
    gpioInterface = GPIOInterface("GPIO", i2c1, addr=0x20, config=[(0x00, 0x00), (0x01, 0xff), (0x03, 0xff), (0x0d, 0xff)])
#    applianceInterface = ApplianceInterface("Lights", gpioInterface)
    
    # Lights
    sensors.addRes(HAControl("testLight", gpioInterface, GPIOAddr(0,0,0), type="light", group="Lights", label="Test light"))
    sensors.addRes(HASensor("testSwitch", gpioInterface, GPIOAddr(0,1,0), type="light", group="Lights", label="Test switch"))

    # Schedules

    # Start interfaces
    gpioInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

