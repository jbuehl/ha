restIgnore = []
restPort = 7377
restPortControl = 7378
xmas = False

import time
import copy
from ha import *
from ha.interfaces.restInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    # resources
    try:
        with open(rootDir+"aliases") as aliasFile:
            aliases = json.load(aliasFile)
    except:
        aliases = {}
    cacheResources = Collection("cacheResources", aliases=aliases)
    localResources = Collection("resources")

    # start the cache to listen for services on other servers
    restIgnore.append(socket.gethostname()+":"+str(restPort))
    restIgnore.append(socket.gethostname()+":"+str(restPortControl))
    restCache = RestProxy("restProxy", cacheResources, ignore=restIgnore, event=stateChangeEvent)
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
    localResources.addRes(Task("bedroomLightsOnSunset", SchedTime(event="sunset"), "bedroomLights", 1, resources=localResources))
    localResources.addRes(Task("bedroomLightsOffSunrise", SchedTime(event="sunrise"), "bedroomLights", 0, resources=localResources))
    localResources.addRes(Task("porchLightsOnSunset", SchedTime(event="sunset"), "porchLights", 1, resources=localResources))
    localResources.addRes(Task("outsideLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=localResources))
    localResources.addRes(Task("outsideLightsOffSunrise", SchedTime(event="sunrise"), "outsideLights", 0, resources=localResources))
    if xmas:
        localResources.addRes(Task("xmasLightsOnSunset", SchedTime(event="sunset"), "xmasLights", 1, resources=localResources))
        localResources.addRes(Task("xmasLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=localResources))
        localResources.addRes(Task("xmasLightsOffSunrise", SchedTime(event="sunrise"), "xmasLights", 0, resources=localResources))
        localResources.addRes(Task("xmasTreeOnXmas", SchedTime(month=[12], day=[25], hour=[7], minute=[00]), "xmasTree", 1, resources=localResources))
    
    # Schedule
    schedule = Schedule("schedule")
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

