
import time
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.restProxy import *
from ha.timeInterface import *
from haWeb import *

stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

if __name__ == "__main__":
    # resources
    resources = HACollection("resources")

    # time resources
    timeInterface = TimeInterface("time")
    resources.addRes(HASensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(HASensor("theDate", timeInterface, "%B %d %Y", type="date", group="Time", label="Date"))
    resources.addRes(HASensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(HASensor("sunrise", timeInterface, "sunrise", type="time", group="Time", label="Sunrise"))
    resources.addRes(HASensor("sunset", timeInterface, "sunset", type="time", group="Time", label="Sunset"))
    resources.addRes(HASensor("theDay", timeInterface, "%a %B %d %Y", type="date", label="Day"))
    resources.addRes(HASensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(HASensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    # start the cache to listen for services on other servers
    restCache = RestProxy("restProxy", resources, socket.gethostname()+":"+str(webRestPort), stateChangeEvent, resourceLock)
    restCache.start()
    time.sleep(30)  # wait for resources to load
    
    # scenes
    resources.addRes(HAScene("outsideLights", [resources["frontLight"],
                                               resources["backLights"],
                                               resources["garageBackDoorLight"]], 
                                               group="Lights", label="Outside lights"))
    resources.addRes(HAScene("bedroomLights", [resources["bedroomLight"], 
                                               resources["bathroomLight"]], 
                                               stateList=[[0, 100, 0], [0, 100, 10]], type="nightLight", group="Lights", label="Night lights"))

    # Tasks
    resources.addRes(HATask("bedroomLightsOnSunset", HASchedTime(event="sunset"), resources["bedroomLights"], 1))
    resources.addRes(HATask("bedroomLightsOffSunrise", HASchedTime(event="sunrise"), resources["bedroomLights"], 0))
    resources.addRes(HATask("outsideLightsOnSunset", HASchedTime(event="sunset"), resources["outsideLights"], 1))
    resources.addRes(HATask("outsideLightsOffMidnight", HASchedTime(hour=[23,0], minute=[00]), resources["outsideLights"], 0))
    resources.addRes(HATask("outsideLightsOffSunrise", HASchedTime(event="sunrise"), resources["outsideLights"], 0))
    resources.addRes(HATask("hotWaterRecircOn", HASchedTime(hour=[05], minute=[0]), resources["recircPump"], 1))
    resources.addRes(HATask("hotWaterRecircOff", HASchedTime(hour=[23], minute=[0]), resources["recircPump"], 0))
    
    # Schedule
    schedule = HASchedule("schedule")
    schedule.addTask(resources["bedroomLightsOnSunset"])
    schedule.addTask(resources["bedroomLightsOffSunrise"])
    schedule.addTask(resources["outsideLightsOnSunset"])
    schedule.addTask(resources["outsideLightsOffMidnight"])
    schedule.addTask(resources["outsideLightsOffSunrise"])
    schedule.addTask(resources["hotWaterRecircOn"])
    schedule.addTask(resources["hotWaterRecircOff"])
    schedule.start()

    # set up the web server
    webInit(resources, restCache, stateChangeEvent, resourceLock)
    
    # start the REST server for this service
    restServer = RestServer(resources, port=webRestPort, event=stateChangeEvent)
    restServer.start()

