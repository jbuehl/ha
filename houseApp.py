restIgnore = []
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
    resources = Collection("resources", aliases=aliases)

    # start the cache to listen for services on other servers
    restCache = RestProxy("restProxy", resources, ignore=restIgnore, event=stateChangeEvent)
    restCache.start()
    
    # scenes and groups
    porchLights = ControlGroup("porchLights", ["frontLights",
                                               "sculptureLights",
                                               "backLights",
                                               "garageBackDoorLight"],
                                               resources=resources, 
                                               type="light", group="Lights", label="Porch lights")
    xmasLights = ControlGroup("xmasLights", ["xmasTree",
                                                "xmasCowTree",
                                                "xmasFrontLights",
                                                "xmasBackLights"],
                                               resources=resources, 
                                               type="light", group=["Lights", "Xmas"], label="Xmas lights")
    bedroomLights = ControlGroup("bedroomLights", ["bedroomLight", 
                                               "bathroomLight"],
                                               resources=resources, 
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
                                               resources=resources, 
                                               type="light", group="Lights", label="Outside lights")
    resources.addRes(porchLights)
    resources.addRes(xmasLights)
    resources.addRes(bedroomLights)
    resources.addRes(outsideLights)
    
    # Tasks
    resources.addRes(Task("bedroomLightsOnSunset", SchedTime(event="sunset"), "bedroomLights", 1, resources=resources))
    resources.addRes(Task("bedroomLightsOffSunrise", SchedTime(event="sunrise"), "bedroomLights", 0, resources=resources))
    resources.addRes(Task("porchLightsOnSunset", SchedTime(event="sunset"), "porchLights", 1, resources=resources))
    resources.addRes(Task("outsideLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=resources))
    resources.addRes(Task("outsideLightsOffSunrise", SchedTime(event="sunrise"), "outsideLights", 0, resources=resources))
    if xmas:
        resources.addRes(Task("xmasLightsOnSunset", SchedTime(event="sunset"), "xmasLights", 1, resources=resources))
        resources.addRes(Task("xmasLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=resources))
        resources.addRes(Task("xmasLightsOffSunrise", SchedTime(event="sunrise"), "xmasLights", 0, resources=resources))
#        resources.addRes(Task("xmasTreeOnXmas", SchedTime(month=[12], day=[25], hour=[7], minute=[00]), "xmasTree", 1, resources=resources))
    
    # Schedule
    schedule = Schedule("schedule")
    schedule.addTask(resources["bedroomLightsOnSunset"])
    schedule.addTask(resources["bedroomLightsOffSunrise"])
    schedule.addTask(resources["porchLightsOnSunset"])
    schedule.addTask(resources["outsideLightsOffMidnight"])
    schedule.addTask(resources["outsideLightsOffSunrise"])
    if xmas:
        schedule.addTask(resources["xmasLightsOnSunset"])
        schedule.addTask(resources["xmasLightsOffMidnight"])
        schedule.addTask(resources["xmasLightsOffSunrise"])
#        schedule.addTask(resources["xmasTreeOnXmas"])
    schedule.start()

    # start the REST server for this service
    restServer = RestServer("house", resources, port=restServicePort, event=stateChangeEvent, label="House")
    restServer.start()

