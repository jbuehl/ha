from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.restServer import *

def frontLightSwitch(sensor, state):
    log(sensor.name, "state:", state)
#    sensors["frontLights"].setState(state)
    
if __name__ == "__main__":
    global sensors
    resources = HACollection("resources")
    schedule = HASchedule("schedule")
    resources.addRes(schedule)

    # Interfaces
    i2c1 = I2CInterface("I2C1", 1)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL+1, 0x7f)])
    
    # Lights
    resources.addRes(HAControl("frontLights", gpio0, GPIOAddr(0,0,0), type="light", group="Lights", label="Front lights"))
    resources.addRes(HAControl("garageBackDoorLight", gpio0, GPIOAddr(0,0,1), type="light", group="Lights", label="Garage back door light"))
    resources.addRes(HASensor("frontLightSwitch", gpio1, GPIOAddr(0,1,0), type="light", group="Lights", label="Front light switch", interrupt=frontLightSwitch))
#    resources.addRes(HAControl("testLight", gpio0, GPIOAddr(0,0,7), type="light", group="Lights", label="Test output"))
#    resources.addRes(HASensor("testSwitch", gpio1, GPIOAddr(0,1,7), type="light", group="Lights", label="Test input"))
    resources.addRes(HAScene("garageLights", [resources["frontLights"],
                                             resources["garageBackDoorLight"]], group="Lights", label="Garage"))

    # Water
    resources.addRes(HAControl("recircPump", gpio0, GPIOAddr(0,0,3), type="hotwater", group="Water", label="Hot water"))

    # Schedules
    schedule.addTask(HATask("Garage lights on sunset", HASchedTime(event="sunset"), resources["garageLights"], 1))
    schedule.addTask(HATask("Garage lights off midnight", HASchedTime(hour=[23,0], minute=[00]), resources["garageLights"], 0))
    schedule.addTask(HATask("Garage lights off sunrise", HASchedTime(event="sunrise"), resources["garageLights"], 0))
    schedule.addTask(HATask("Hot water recirc on", HASchedTime(hour=[05], minute=[0]), resources["recircPump"], 1))
    schedule.addTask(HATask("Hot water recirc off", HASchedTime(hour=[23], minute=[0]), resources["recircPump"], 0))

    # Start interfaces
    gpio0.start()
    gpio1.start()
    schedule.start()
    restServer = RestServer(resources)
    restServer.start()

