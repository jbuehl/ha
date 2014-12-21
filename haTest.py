from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.applianceInterface import *
from ha.restServer import *

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    gpioInterface = GPIOInterface("GPIO")
    applianceInterface = ApplianceInterface("Lights", gpioInterface)
    
    # Lights
    sensors.addRes(HAControl("testLight", applianceInterface, 0, type="light", group="Lights", label="Test light"))
    sensors.addRes(HASensor("testSwitch", applianceInterface, 1, type="light", group="Lights", label="Test switch"))

    # Schedules

    # Start interfaces
    applianceInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

