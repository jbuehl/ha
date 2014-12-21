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
    lightInterface = LightInterface("Garage", gpioInterface)
    
    # Lights
    sensors.addRes(HAControl("frontLights", lightInterface, 0, type="light", group="Lights", label="Front lights"))
    sensors.addRes(HAControl("garageBackDoorLight", lightInterface, 1, type="light", group="Lights", label="Garage back door light"))
#    sensors.addRes(HASensor("garageBackDoorSwitch", lightInterface, 1, type="light", group="Lights", label="Garage back door switch"))
    sensors.addRes(HAScene("garageLights", [sensors["frontLights"],
                                             sensors["garageBackDoorLight"]], [[0,1], [0,1]], group="Lights", label="Garage"))

    # Schedules
    schedule.addTask(HATask("Garage lights on sunset", HASchedTime(event="sunset"), sensors["garageLights"], 1))
    schedule.addTask(HATask("Garage lights off midnight", HASchedTime(hour=[23,0], minute=[00]), sensors["garageLights"], 0))
    schedule.addTask(HATask("Garage lights off sunrise", HASchedTime(event="sunrise"), sensors["garageLights"], 0))

    # Start interfaces
    lightInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

