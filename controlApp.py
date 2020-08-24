
restWatch = ["garage", "holiday", "hvac", "house", "backhouse", "pool"]
espRestWatch = ["frontLights", "backLights", "garageBackDoorLight", "familyRoomLamp", "bedroomLight", "bathroomLight"]
defaultConfig = {
}

from ha import *
from ha.interfaces.fileInterface import *
from ha.interfaces.tplinkInterface import *
from ha.interfaces.samsungInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *
from ha.rest.restProxy1 import *

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
    restCache = RestProxy("restProxy", cacheResources, watch=restWatch, event=stateChangeEvent)
    restCache.start()
    # start the cache to listen for legacy services on ESP devices
    espRestCache = RestProxy1("espRestCache", cacheResources, watch=espRestWatch, event=stateChangeEvent)
    espRestCache.start()

    # proxied light controls
    frontLights = ProxySensor("frontLights", cacheResources)
    sculptureLights = ProxySensor("sculptureLights", cacheResources)
    holidayLights = ProxySensor("holidayLights", cacheResources)
    garageBackDoorLight = ProxySensor("garageBackDoorLight", cacheResources)
    familyRoomLamp = ProxySensor("familyRoomLamp", cacheResources)
    bedroomLight = ProxySensor("bedroomLight", cacheResources)
    bathroomLight = ProxySensor("bathroomLight", cacheResources)
    poolLights = ProxySensor("poolLights", cacheResources)

    # proxied xmas light controls
    xmasTree = ProxySensor("xmasTree", cacheResources)
    xmasWindowLights = ProxySensor("xmasWindowLights", cacheResources)
    xmasFireplaceLights = ProxySensor("xmasFireplaceLights", cacheResources)
    xmasBackLights = ProxySensor("xmasBackLights", cacheResources)

    # proxied garage controls
    recircPump = ProxySensor("recircPump", cacheResources)
    hotWaterRecirc = ProxySensor("hotWaterRecirc", cacheResources)

    # proxied hvac controls
    backHeatTempTarget = ProxySensor("backHeatTempTarget", cacheResources)
    backCoolTempTarget = ProxySensor("backCoolTempTarget", cacheResources)
    backHeatTempUpMorning = ProxySensor("backHeatTempUpMorning", cacheResources)
    backHeatTempDownMorning = ProxySensor("backHeatTempDownMorning", cacheResources)
    backHeatTempDownEvening = ProxySensor("backHeatTempDownEvening", cacheResources)
    northHeatTempTarget = ProxySensor("northHeatTempTarget", cacheResources)
    northCoolTempTarget = ProxySensor("northCoolTempTarget", cacheResources)
    northHeatTempUpMorning = ProxySensor("northHeatTempUpMorning", cacheResources)
    northHeatTempDownMorning = ProxySensor("northHeatTempDownMorning", cacheResources)
    northHeatTempDownEvening = ProxySensor("northHeatTempDownEvening", cacheResources)
    southHeatTempTarget = ProxySensor("southHeatTempTarget", cacheResources)
    southCoolTempTarget = ProxySensor("southCoolTempTarget", cacheResources)
    southHeatTempUpMorning = ProxySensor("southHeatTempUpMorning", cacheResources)
    southHeatTempDownMorning = ProxySensor("southHeatTempDownMorning", cacheResources)
    southHeatTempDownEvening = ProxySensor("southHeatTempDownEvening", cacheResources)

    # proxied alert controls
    alertDoors = ProxySensor("alertDoors", cacheResources)
    alertMotion = ProxySensor("alertMotion", cacheResources)

    # light groups
    porchLights = ControlGroup("porchLights", [frontLights,
                                               sculptureLights,
                                               holidayLights,
                                               backLights,
                                               garageBackDoorLight,
                                               familyRoomLamp],
                                           type="light", group="Lights", label="Porch lights")
    xmasLights = ControlGroup("xmasLights", [xmasTree,
                                             xmasWindowLights,
                                             xmasFireplaceLights,
                                             xmasBeamLights,
                                             xmasBackLights],
                                           type="light", group=["Lights", "Xmas"], label="Xmas lights")
    nightLights = ControlGroup("nightLights", [bedroomLight,
                                               bathroomLight],
                                               stateList=[[0, 30, 0], [0, 100, 10]],
                                               type="nightLight", group="Lights", label="Night lights")
    outsideLights = ControlGroup("outsideLights", [frontLights,
                                                   sculptureLights,
                                                   backLights,
                                                   garageBackDoorLight,
                                                   # bbqLights,
                                                   # backYardLights,
                                                   deckLights,
                                                   trashLights,
                                                   garageLights,
                                                   poolLights,
                                                   familyRoomLamp,
                                                   holidayLights,
                                                   xmasTree,
                                                   xmasWindowLights,
                                                   xmasTree,
                                                   xmasFireplaceLights,
                                                   xmasBeamLights,
                                                   xmasBackLights],
                                               type="light", group="Lights", label="Outside lights")

    # mode groups
    guestMode = ControlGroup("guestMode", [backHouseMusic,
                                           backHeatTempTarget,
                                           backCoolTempTarget,
                                           backHeatTempUpMorning,
                                           backHeatTempDownMorning,
                                           backHeatTempDownEvening],
                                       resources=cacheResources, stateMode=True,
                                       stateList=[[0, 1],
                                                 [60, 66], [80, 75],
                                                 [0, 1], [0, 1], [0, 1]],
                                       group=["Modes", "BackHouse"], label="Guest")
    vacationMode = ControlGroup("vacationMode", [alertDoors,
                                                 alertMotion,
                                                 recircPump,
                                                 hotWaterRecirc,
                                                 northHeatTempTarget,
                                                 northCoolTempTarget,
                                                 northHeatTempUpMorning,
                                                 northHeatTempDownMorning,
                                                 northHeatTempDownEvening,
                                                 southHeatTempTarget,
                                                 southCoolTempTarget,
                                                 southHeatTempUpMorning,
                                                 southHeatTempDownMorning,
                                                 southHeatTempDownEvening],
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

    restServer = RestServer("control", resources, port=7379, event=stateChangeEvent, label="Control", multicast=True)

    # Start interfaces
    configData.start()
    schedule.start()
    restServer.start()
