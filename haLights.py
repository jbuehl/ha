restIgnore = []
restPort = 7377
restPortControl = 7378
xmas = False

import time
import copy
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.restProxy import *

stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

if __name__ == "__main__":
    # resources
    try:
        with open(rootDir+"aliases") as aliasFile:
            aliases = json.load(aliasFile)
    except:
        aliases = {}
    cacheResources = HACollection("cacheResources", aliases=aliases)
    localResources = HACollection("resources")

    # start the cache to listen for services on other servers
    restIgnore.append(socket.gethostname()+":"+str(restPort))
    restIgnore.append(socket.gethostname()+":"+str(restPortControl))
    restCache = RestProxy("restProxy", cacheResources, restIgnore, stateChangeEvent, resourceLock)
    restCache.start()
    
    # scenes and groups
    porchLights = ControlGroup("porchLights", ["frontLights",
                                               "sculptureLights",
                                               "backLights",
                                               "garageBackDoorLight"],
                                               resources=cacheResources, 
                                               type="light", group="Lights", label="Porch lights")
    xmasLights = ControlGroup("xmasLights", ["xmasTree",
                                                "xmasCowTree",
                                                "xmasFrontLights",
                                                "xmasBackLights"],
                                               resources=cacheResources, 
                                               type="light", group="Lights", label="Xmas lights")
    bedroomLights = ControlGroup("bedroomLights", ["bedroomLight", 
                                               "bathroomLight"],
                                               resources=cacheResources, 
                                               stateList=[[0, 100, 0], [0, 100, 10]], 
                                               type="nightLight", group="Lights", label="Night lights")
    outsideLights = ControlGroup("outsideLights", ["frontLights",
                                               "sculptureLights",
                                               "backLights",
                                               "garageBackDoorLight",
                                               "bbqLights",
                                               "backYardLights",
                                               "deckLights",
                                               "trashLights",
                                               "xmasTree",
                                               "xmasCowTree",
                                               "xmasFrontLights",
                                               "xmasBackLights"],
                                               resources=cacheResources, 
                                               type="light", group="Lights", label="Outside lights")
    localResources.addRes(porchLights)
    localResources.addRes(xmasLights)
    localResources.addRes(bedroomLights)
    localResources.addRes(outsideLights)
    
    # Tasks
    localResources.addRes(HATask("bedroomLightsOnSunset", HASchedTime(event="sunset"), "bedroomLights", 1, resources=localResources))
    localResources.addRes(HATask("bedroomLightsOffSunrise", HASchedTime(event="sunrise"), "bedroomLights", 0, resources=localResources))
    localResources.addRes(HATask("porchLightsOnSunset", HASchedTime(event="sunset"), "porchLights", 1, resources=localResources))
    localResources.addRes(HATask("outsideLightsOffMidnight", HASchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=localResources))
    localResources.addRes(HATask("outsideLightsOffSunrise", HASchedTime(event="sunrise"), "outsideLights", 0, resources=localResources))
    if xmas:
        localResources.addRes(HATask("xmasLightsOnSunset", HASchedTime(event="sunset"), "xmasLights", 1, resources=localResources))
        localResources.addRes(HATask("xmasLightsOffMidnight", HASchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=localResources))
        localResources.addRes(HATask("xmasLightsOffSunrise", HASchedTime(event="sunrise"), "xmasLights", 0, resources=localResources))
        localResources.addRes(HATask("xmasTreeOnXmas", HASchedTime(month=[12], day=[25], hour=[7], minute=[00]), "xmasTree", 1, resources=localResources))
    
    # Schedule
    schedule = HASchedule("schedule")
    schedule.addTask(localResources["bedroomLightsOnSunset"])
    schedule.addTask(localResources["bedroomLightsOffSunrise"])
    schedule.addTask(localResources["porchLightsOnSunset"])
    schedule.addTask(localResources["outsideLightsOffMidnight"])
    schedule.addTask(localResources["outsideLightsOffSunrise"])
    if xmas:
        schedule.addTask(localResources["xmasLightsOnSunset"])
        schedule.addTask(localResources["xmasLightsOffMidnight"])
        schedule.addTask(localResources["xmasLightsOffSunrise"])
        schedule.addTask(localResources["xmasTreeOnXmas"])
    schedule.start()

    # start the REST server for this service
    restServer = RestServer(localResources, port=restPort, event=stateChangeEvent, label="Lights")
    restServer.start()

