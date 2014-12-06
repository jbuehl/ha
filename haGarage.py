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
    sensors.addRes(HAControl("garageBackDoorLight", lightInterface, 0, type="light", group="Lights", label="Garage back door light"))
#    sensors.addRes(HASensor("garageBackDoorSwitch", lightInterface, 1, type="light", group="Lights", label="Garage back door switch"))

    # Schedules
    schedule.addTask(HATask("Garage back light on sunset", HASchedTime(event="sunset"), sensors["garageBackDoorLight"], 1))
    schedule.addTask(HATask("Garage back light off midnight", HASchedTime(hour=[23,0], minute=[00]), sensors["garageBackDoorLight"], 0))
    schedule.addTask(HATask("Garage back light off sunrise", HASchedTime(event="sunrise"), sensors["garageBackDoorLight"], 0))

    # Start interfaces
    lightInterface.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

