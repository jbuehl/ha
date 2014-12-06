from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.lightInterface import *
from ha.restServer import *

if __name__ == "__main__":
    resources = HACollection("resources")
    sensors = HACollection("sensors")
    schedule = HASchedule("schedule")
    resources.addRes(sensors)
    resources.addRes(schedule)

    # Interfaces
    gpioInterface = GPIOInterface("GPIO")
    lightInterface = LightInterface("Lights", gpioInterface)
    
    # Lights
    sensors.addRes(HAControl("testLight", lightInterface, 0, type="light", group="Lights", label="Test light"))
    sensors.addRes(HASensor("testSwitch", lightInterface, 1, type="light", group="Lights", label="Test switch"))

    # Schedules

    # Start interfaces
    lightInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

