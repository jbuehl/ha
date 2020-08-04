
restWatch = ["garage", "holiday", "hvac", "backhouse", "pool",
            "frontLights", "backLights", "garageBackDoorLight", "familyRoomLamp", "bedroomLight", "bathroomLight",
            "frontPorchMotionSensor", "drivewayMotionSensor", "southSideMotionSensor", "deckMotionSensor", "backHouseMotionSensor", "northSideMotionSensor"]
restIgnore = ["house", "power"]
defaultConfig = {

}

from ha import *
from ha.interfaces.fileInterface import *
from ha.interfaces.tplinkInterface import *
from ha.interfaces.samsungInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    tplinkInterface = TplinkInterface("tplinkInterface", event=stateChangeEvent)
    samsungInterface = SamsungInterface("samsungInterface", event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"control.state", event=stateChangeEvent, initialState=defaultConfig)

    # Controls
    garageLights = Control("garageLights", tplinkInterface, "192.168.1.115", type="light", group=["Lights", "Garage"], label="Garage lights")
    deckLights = Control("deckLights", tplinkInterface, "192.168.1.128", type="light", group=["Lights", "Garage"], label="Deck lights")
    trashLights = Control("trashLights", tplinkInterface, "192.168.1.133", type="light", group=["Lights", "Garage"], label="Trash lights")
    backLights = Control("backLights", tplinkInterface, "192.168.1.148", type="light", group=["Lights", "Garage"], label="Back lights")
    backHouseMusic = Control("backHouseMusic", tplinkInterface, "192.168.1.117", type="plug", group=["AV", "BackHouse"], label="Back house music")
    xmasBeamLights = Control("xmasBeamLights", tplinkInterface, "192.168.1.119", type="light", group="Lights", label="Xmas beam lights")
    tv = Control("tv", samsungInterface, "192.168.1.103", type="tv", group=["AV", "FamilyRoom"], label="Family room TV")

    # Wifi signal strengths
    garageLightsRssi = Control("garageLights-rssi", tplinkInterface, "192.168.1.115,rssi", type="dBm", group="Network", label="Garage lights rssi")
    deckLightsRssi = Control("deckLights-rssi", tplinkInterface, "192.168.1.128,rssi", type="dBm", group="Network", label="Deck lights rssi")
    trashLightsRssi = Control("trashLights-rssi", tplinkInterface, "192.168.1.133,rssi", type="dBm", group="Network", label="Trash lights rssi")
    backLightsRssi = Control("backLights-rssi", tplinkInterface, "192.168.1.148,rssi", type="dBm", group="Network", label="Back lights rssi")
    backHouseMusicRssi = Control("backHouseMusic-rssi", tplinkInterface, "192.168.1.117,rssi", type="dBm", group="Network", label="Back house music rssi")
    xmasBeamLightsRssi = Control("xmasBeamLights-rssi", tplinkInterface, "192.168.1.119,rssi", type="dBm", group="Network", label="Xmas Beam lights rssi")

    # start the cache to listen for services on other servers
    cacheResources = Collection("cacheResources", event=stateChangeEvent)
    restCache = RestProxy("restProxy", cacheResources, watch=restWatch, ignore=restIgnore, event=stateChangeEvent)
    restCache.start()

    # add local resources to cache resource list
    cacheResources.addRes(garageLights)
    cacheResources.addRes(deckLights)
    cacheResources.addRes(trashLights)
    cacheResources.addRes(backLights)
    cacheResources.addRes(backHouseMusic)
    cacheResources.addRes(xmasBeamLights)

    # light groups
    porchLights = ControlGroup("porchLights", ["frontLights",
                                               "sculptureLights",
                                               "holidayLights",
                                               "backLights",
                                               "garageBackDoorLight",
                                               "familyRoomLamp"],
                                           resources=cacheResources,
                                           type="light", group="Lights", label="Porch lights")
    xmasLights = ControlGroup("xmasLights", ["xmasTree",
                                             "xmasWindowLights",
                                             "xmasTree",
                                             "xmasFireplaceLights",
                                             "xmasBeamLights",
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
                                                   "familyRoomLamp",
                                                   "holidayLights",
                                                   "xmasTree",
                                                   "xmasWindowLights",
                                                   "xmasTree",
                                                   "xmasFireplaceLights",
                                                   "xmasBeamLights",
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
                                       group=["Modes", "BackHouse"], label="Guest")
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
                                                   garageLightsRssi, deckLightsRssi, trashLightsRssi, backLightsRssi,
                                                   xmasBeamLights, xmasBeamLightsRssi,
                                                   porchLights, xmasLights, nightLights, outsideLights,
                                                   guestMode, vacationMode, tv,
                                                   backHouseMusic, backHouseMusicRssi], event=stateChangeEvent)

    # Light tasks
    resources.addRes(Task("nightLightsOnSunset", SchedTime(event="sunset"), "nightLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("nightLightsOffSunrise", SchedTime(event="sunrise"), "nightLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("lightsOnSunset", SchedTime(event="sunset"), "porchLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("lightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("lightsOffSunrise", SchedTime(event="sunrise"), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOnSunset", SchedTime(event="sunset"), "xmasLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffSunrise", SchedTime(event="sunrise"), "xmasLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("fireplaceOffMidnight", SchedTime(hour=[23,0], minute=[00]), "fireplace", 0, resources=resources, group="Lights"))
    #        resources.addRes(Task("xmasTreeOnXmas", SchedTime(month=[12], day=[25], hour=[7], minute=[00]), "xmasTree", 1, resources=resources))

    # ESP servers being proxied
    resources.addRes(cacheResources["frontLights"])
    resources.addRes(cacheResources["backLights"])
    resources.addRes(cacheResources["garageBackDoorLight"])
    resources.addRes(cacheResources["familyRoomLamp"])
    resources.addRes(cacheResources["bedroomLight"])
    resources.addRes(cacheResources["bathroomLight"])
    resources.addRes(cacheResources["frontPorchMotionSensor"])
    resources.addRes(cacheResources["drivewayMotionSensor"])
    resources.addRes(cacheResources["southSideMotionSensor"])
    resources.addRes(cacheResources["deckMotionSensor"])
    resources.addRes(cacheResources["backHouseMotionSensor"])
    resources.addRes(cacheResources["northSideMotionSensor"])

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
    schedule.addTask(resources["fireplaceOffMidnight"])
    #        schedule.addTask(resources["xmasTreeOnXmas"])

    restServer = RestServer("control", resources, port=7379, event=stateChangeEvent, label="Control app", multicast=True)

    # Start interfaces
    configData.start()
    schedule.start()
    restServer.start()
