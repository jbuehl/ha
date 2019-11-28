
restWatch = []
restIgnore = ["house", "power"]
defaultConfig = {

}

from ha import *
from ha.interfaces.fileInterface import *
from ha.interfaces.tplinkInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    tplinkInterface = TplinkInterface("tplinkInterface", event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"control.state", event=stateChangeEvent, initialState=defaultConfig)

    # Controls
    garageLights = Control("garageLights", tplinkInterface, "192.168.1.115", type="light", group=["Lights", "Garage"], label="Garage lights")
    deckLights = Control("deckLights", tplinkInterface, "192.168.1.128", type="light", group=["Lights", "Garage"], label="Deck lights")
    trashLights = Control("trashLights", tplinkInterface, "192.168.1.133", type="light", group=["Lights", "Garage"], label="Trash lights")
    backLights = Control("backLights", tplinkInterface, "192.168.1.148", type="light", group=["Lights", "Garage"], label="Back lights")
    backHouseMusic = Control("backHouseMusic", tplinkInterface, "192.168.1.117", type="plug", group=["Plugs", "Backhouse"], label="Back house music")
    plugControl = Control("plugControl", tplinkInterface, "192.168.1.135", type="plug", group="Lights", label="Plug control")

    # Wifi signal strengths
    garageLightsRssi = Control("garageLights-rssi", tplinkInterface, "192.168.1.115,rssi", type="dBm", group="Network", label="Garage lights rssi")
    deckLightsRssi = Control("deckLights-rssi", tplinkInterface, "192.168.1.128,rssi", type="dBm", group="Network", label="Deck lights rssi")
    trashLightsRssi = Control("trashLights-rssi", tplinkInterface, "192.168.1.133,rssi", type="dBm", group="Network", label="Trash lights rssi")
    backLightsRssi = Control("backLights-rssi", tplinkInterface, "192.168.1.148,rssi", type="dBm", group="Network", label="Back lights rssi")
    backHouseMusicRssi = Control("backHouseMusic-rssi", tplinkInterface, "192.168.1.117,rssi", type="dBm", group="Network", label="Back house music rssi")
    plugControlRssi = Control("plugControl-rssi", tplinkInterface, "192.168.1.135,rssi", type="plug", group="Network", label="Plug control rssi")

    # start the cache to listen for services on other servers
    cacheResources = Collection("cacheResources")
    restCache = RestProxy("restProxy", cacheResources, watch=restWatch, ignore=restIgnore, event=stateChangeEvent)
    restCache.start()

    # light groups
    porchLights = ControlGroup("porchLights", ["frontLights",
                                               "sculptureLights",
                                               "holidayLights",
                                               "backLights",
                                               "garageBackDoorLight"],
                                           resources=cacheResources,
                                           type="light", group="Lights", label="Porch lights")
    xmasLights = ControlGroup("xmasLights", ["xmasTree",
                                             "xmasCowTree",
                                             "xmasBackLights"],
                                           resources=cacheResources,
                                           type="light", group=["Lights", "Xmas"], label="Xmas lights")
    nightLights = ControlGroup("nightLights", ["bedroomLight",
                                               "bathroomLight"],
                                               resources=cacheResources,
                                               stateList=[[0, 30, 0], [0, 100, 10]],
                                               type="nightLight", group="Lights", label="Night lights")
    outsideLights = ControlGroup("outsideLights", ["frontLights",
                                                   "sculptureLights",
                                                   "backLights",
                                                   "garageBackDoorLight",
                                                   "bbqLights",
                                                   "backYardLights",
                                                   "deckLights",
                                                   "trashLights",
                                                   "garageLight",
                                                   "poolLights",
                                                   "holidayLights",
                                                   "xmasTree",
                                                   "xmasCowTree",
                                                   "xmasBackLights"],
                                               resources=cacheResources,
                                               type="light", group="Lights", label="Outside lights")
    guestMode = ControlGroup("guestMode", ["backHouseMusic",
                                           "backHeatTempTarget",
                                           "backCoolTempTarget",
                                           "backHeatTempUpMorning",
                                           "backHeatTempDownMorning",
                                           "backHeatTempDownEvening"],
                                       resources=cacheResources, stateMode=True,
                                       stateList=[[0, 1],
                                                 [60, 66], [80, 75],
                                                 [0, 1], [0, 1], [0, 1]],
                                       group="Modes", label="Guest")
    vacationMode = ControlGroup("vacationMode", ["alertDoors",
                                                 "recircPump",
                                                 "hotWaterRecirc",
                                                 "northHeatTempTarget",
                                                 "northCoolTempTarget",
                                                 "northHeatTempUpMorning",
                                                 "northHeatTempDownMorning",
                                                 "northHeatTempDownEvening",
                                                 "southHeatTempTarget",
                                                 "southCoolTempTarget",
                                                 "southHeatTempUpMorning",
                                                 "southHeatTempDownMorning",
                                                 "southHeatTempDownEvening"],
                                               resources=cacheResources, stateMode=True,
                                               stateList=[[0, 1],
                                                          [1, 0], [1, 0],
                                                          [66, 60], [75, 80],
                                                          [1, 0], [1, 0], [1, 0],
                                                          [66, 60], [75, 80],
                                                          [1, 0], [1, 0], [1, 0]],
                                               group="Modes", label="Vacation")
    # Resources
    resources = Collection("resources", resources=[garageLights, deckLights, trashLights, backLights,
                                                   garageLightsRssi, deckLightsRssi, trashLightsRssi,
                                                   plugControl, plugControlRssi,
                                                   porchLights, xmasLights, nightLights, outsideLights,
                                                   guestMode, vacationMode,
                                                   backHouseMusic, backHouseMusicRssi])

    # Light tasks
    resources.addRes(Task("nightLightsOnSunset", SchedTime(event="sunset"), "nightLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("nightLightsOffSunrise", SchedTime(event="sunrise"), "nightLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("lightsOnSunset", SchedTime(event="sunset"), "porchLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("lightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("lightsOffSunrise", SchedTime(event="sunrise"), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOnSunset", SchedTime(event="sunset"), "xmasLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffSunrise", SchedTime(event="sunrise"), "xmasLights", 0, resources=resources, group="Lights"))
    #        resources.addRes(Task("xmasTreeOnXmas", SchedTime(month=[12], day=[25], hour=[7], minute=[00]), "xmasTree", 1, resources=resources))

    # Schedule
    schedule = Schedule("schedule")
    schedule.addTask(resources["nightLightsOnSunset"])
    schedule.addTask(resources["nightLightsOffSunrise"])
    schedule.addTask(resources["lightsOnSunset"])
    schedule.addTask(resources["lightsOffMidnight"])
    schedule.addTask(resources["lightsOffSunrise"])
    schedule.addTask(resources["xmasLightsOnSunset"])
    schedule.addTask(resources["xmasLightsOffMidnight"])
    schedule.addTask(resources["xmasLightsOffSunrise"])
    #        schedule.addTask(resources["xmasTreeOnXmas"])

    restServer = RestServer("control", resources, port=7379, event=stateChangeEvent, label="Control app")

    # Start interfaces
    configData.start()
    schedule.start()
    restServer.start()
