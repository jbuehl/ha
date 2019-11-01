
stringLength = 343
defaultConfig = {
    "holiday": "None",
}
restWatch = []
restIgnore = ["house", "hvac", "power", "solar", "carcharger", "sprinklers"]

from ha import *
from ha.interfaces.neopixelInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.tc74Interface import *
from ha.interfaces.tempInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *
from ha.rest.restProxy import *

# dictionary of patterns
patterns = {"onPattern": [on],
            "offPattern": [off],
            "whitePattern": [white],
            "pinkPattern": [pink],
            "redPattern": [red],
            "orangePattern": [orange],
            "yellowPattern": [yellow],
            "greenPattern": [green],
            "bluePattern": [blue],
            "purplePattern": [purple],
            "cyanPattern": [cyan],
            "magentaPattern": [magenta],
            "rustPattern": [rust],
            "indigoPattern": [indigo],
            "christmasPattern": 3*[red]+3*[green],
            "hanukkahPattern": 7*[blue]+3*[white],
            "halloweenPattern": 5*[orange]+3*[rust]+2*[purple],
            "valentinesPattern": 1*[white]+2*[pink]+5*[red]+2*[pink],
            "stpatricksPattern": [green],
            "maydayPattern": [red],
            "mardigrasPattern": 3*[purple]+3*[yellow]+3*[green],
            "presidentsPattern": 3*[red]+3*[white]+3*[blue],
            "july4Pattern": 5*[red]+5*[white]+5*[blue],
            "bastillePattern": 10*[red]+10*[white]+10*[blue],
            "cincodemayoPattern": 10*[green]+10*[white]+10*[red],
            "easterPattern": [yellow]+[blue]+[green]+[cyan]+[magenta],
            "swedenPattern": 5*[blue]+5*[yellow],
            "canadaPattern": 5*[red]+5*[white],
            "fallPattern": 5*[red]+5*[orange]+5*[rust]+5*[orange],
            "pridePattern": [pink]+[red]+[orange]+[yellow]+[green]+[blue]+[purple],
            "holiPattern": [red]+[yellow]+[blue]+[green]+[orange]+[purple]+[pink]+[magenta],
            "maydayPattern": [red],
            "columbusPattern": [green]+[white]+[red],
            "mlkPattern": [white]+[red]+[yellow]+[rust],
            "spectrumPattern": [red]+[orange]+[yellow]+[green]+[blue]+[purple],
            }

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    neopixelInterface = NeopixelInterface("neopixelInterface", None, length=stringLength, event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"lights.conf", event=stateChangeEvent, initialState=defaultConfig)
    i2c1 = I2CInterface("i2c1", bus=1)
    tc74 = TC74Interface("tc74", i2c1)
    temp = TempInterface("temp", tc74, sample=10)

    # Temperature
    garageTemp = Sensor("garageTemp", temp, 0x4b, group="Temperature", label="Garage temp", type="tempF", event=stateChangeEvent)

    # Light controls
#    leftSegment = ("leftSegment", 0, 112)
#    centerSegment = ("centerSegment", 112, 58)
#    rightSegment = ("rightSegment", 170, 173)
#    allLights = ("allLights", 0, 343)

    offLights = HolidayLightControl("None", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                          pattern=patterns["offPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="None")
    valentinesLights = HolidayLightControl("Valentines day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["valentinesPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Valentines day")
    mardigrasLights = HolidayLightControl("Mardi gras", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["mardigrasPattern"],
                                                           animation=SparkleAnimation(rate=5))],
                                        type="light", group=["Lights", "Holiday"], label="Mardi gras")
    presidentsLights = HolidayLightControl("Presidents day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["presidentsPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Presidents day")
    stpatricksLights = HolidayLightControl("St Patricks day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["stpatricksPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="St Patricks day")
    maydayLights = HolidayLightControl("May day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["maydayPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="May day")
    easterLights = HolidayLightControl("Easter", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["easterPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Easter")
    cincodemayoLights = HolidayLightControl("Cinco de Mayo", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["cincodemayoPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Cinco de mayo")
    swedenLights = HolidayLightControl("Sweden day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["swedenPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Sweden day")
    canadaLights = HolidayLightControl("Canada day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["canadaPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Canada day")
    prideLights = HolidayLightControl("Gay pride", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["pridePattern"],
                                                           animation=SparkleAnimation(rate=3))],
                                        type="light", group=["Lights", "Holiday"], label="Gay pride")
    flagLights = HolidayLightControl("Flag day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["presidentsPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Flag day")
    july4Lights = HolidayLightControl("4th of July", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["july4Pattern"],
                                                           animation=SparkleAnimation(rate=1))],
                                        type="light", group=["Lights", "Holiday"], label="4th of july")
    bastilleLights = HolidayLightControl("Bastille day", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["bastillePattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Bastille day")
    fallLights = HolidayLightControl("Fall", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                          pattern=patterns["fallPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Fall")
    halloweenLights = HolidayLightControl("Halloween", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["halloweenPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Halloween")
    spookyLights = HolidayLightControl("Spooky", neopixelInterface,
                                        segments=[Segment("leftSegment",     0, 112,
                                                           pattern=[orange]),
                                                  Segment("centerSegment", 112,  58,
                                                           pattern=patterns["halloweenPattern"]),
                                                  Segment("rightSegment",  170, 140,
                                                           pattern=[orange],
                                                           animation=FlickerAnimation(rate=1)),
                                                  Segment("farRightSegment", 310, 33,
                                                           pattern=[orange],
                                                           animation=FlickerAnimation())],
                                        type="light", group=["Lights", "Holiday"], label="Spooky")
    electionLights = HolidayLightControl("Election day", neopixelInterface,
                                        segments=[Segment("leftSegment",     0, 112,
                                                           pattern=10*[red]+10*[white]+10*[blue],
                                                           animation=CrawlAnimation(direction=1)),
                                                  Segment("centerSegment", 112,  58,
                                                           pattern=1*[red]+1*[white]+1*[blue],
                                                           animation=SparkleAnimation(rate=1)),
                                                  Segment("rightSegment",  170, 173,
                                                           pattern=10*[red]+10*[white]+10*[blue],
                                                           animation=CrawlAnimation(direction=-1))],
                                        type="light", group=["Lights", "Holiday"], label="Election day")
    christmasLights = HolidayLightControl("Christmas", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["christmasPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Christmas")
    hanukkahLights = HolidayLightControl("Hanukkah", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["hanukkahPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Hanukkah")
    testLights = HolidayLightControl("Test", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["spectrumPattern"],
                                                           animation=CrawlAnimation(direction=1))],
                                        type="light", group=["Lights", "Holiday"], label="Test")

    holidayLightControls = Collection("HolidayLightControls", resources=[offLights, valentinesLights, presidentsLights, mardigrasLights, stpatricksLights,
                           easterLights, maydayLights, cincodemayoLights, swedenLights, prideLights, flagLights, canadaLights, july4Lights, bastilleLights,
                           fallLights, halloweenLights, spookyLights, electionLights, christmasLights, hanukkahLights,
                           testLights])
    # Persistent config data
    holiday = MultiControl("holiday", configData, "holiday", values=list(holidayLightControls.keys()),
                            group=["Lights", "Holiday"], label="Holiday")

# Tasks
    # 2019
    holidayTasks = [
            Task("OffTask",          SchedTime(                              hour=12, minute=0), holiday, "None"),
            Task("valentinesTask",   SchedTime(year=2019, month=Feb, day=[13,14], hour=12, minute=0), holiday, "Valentines day"),
            Task("presidentsTask",   SchedTime(year=2019, month=Feb, day=18, hour=12, minute=0), holiday, "Presidents day"),
            Task("mardigrasTask",    SchedTime(year=2019, month=Mar, day=[2,3,4,5],  hour=12, minute=0), holiday, "Mardi gras"),
            Task("stpatricksTask",   SchedTime(year=2019, month=Mar, day=[16,17], hour=12, minute=0), holiday, "St Patricks day"),
            Task("easterTask",       SchedTime(year=2019, month=Apr, day=[20,21], hour=12, minute=0), holiday, "Easter"),
            Task("maydayTask",       SchedTime(year=2019, month=May, day=1,  hour=12, minute=0), holiday, "May day"),
            Task("cincodemayoTask",  SchedTime(year=2019, month=May, day=5,  hour=12, minute=0), holiday, "Cinco de Mayo"),
            Task("swedenTask",       SchedTime(year=2019, month=Jun, day=6,  hour=12, minute=0), holiday, "Sweden day"),
            Task("prideTask",        SchedTime(year=2019, month=Jun, day=9,  hour=12, minute=0), holiday, "Pride day"),
            Task("flagTask",         SchedTime(year=2019, month=Jun, day=14, hour=12, minute=0), holiday, "Flag day"),
            Task("canadaTask",       SchedTime(year=2019, month=Jul, day=1,  hour=12, minute=0), holiday, "Canada day"),
            Task("july3Task",        SchedTime(year=2019, month=Jul, day=3,  hour=12, minute=0), holiday, "Presidents day"),
            Task("july4Task",        SchedTime(year=2019, month=Jul, day=4,  hour=12, minute=0), holiday, "4th of July"),
            Task("bastilleTask",     SchedTime(year=2019, month=Jul, day=14, hour=12, minute=0), holiday, "Bastille day"),
            Task("fallTask",         SchedTime(year=2019, month=Sep, day=21, hour=12, minute=0), holiday, "Fall"),
            Task("halloweenTask",    SchedTime(year=2019, month=Oct, day=31, hour=12, minute=0), holiday, "Halloween"),
            Task("thanksgivingTask", SchedTime(year=2019, month=Nov, day=28, hour=12, minute=0), holiday, "Fall"),
            Task("christmasTask",    SchedTime(year=2019, month=Dec,         hour=12, minute=0), holiday, "Christmas"),
            Task("hanukkahTask",     SchedTime(year=2019, month=Dec, day=22, hour=12, minute=0), holiday, "Hanukkah"),
            ]

    # Resources
    resources = Collection("resources", resources=[garageTemp])
    holidayLights = AliasControl("holidayLights", None, holidayLightControls, holiday, type="light", group=["Lights", "Holiday"], label="Holiday lights")

    # start the cache to listen for services on other servers
    cacheResources = Collection("cacheResources")
    restCache = RestProxy("restProxy", cacheResources, watch=restWatch, ignore=restIgnore, event=stateChangeEvent)
    restCache.start()

    # light groups
    porchLights = ControlGroup("porchLights", ["frontLights",
                                               "sculptureLights",
                                               "holidayLights",
                                               "backLights",
                                               # "deckLights",
                                               "garageBackDoorLight"],
                                               resources=cacheResources,
                                               type="light", group="Lights", label="Porch lights")
    xmasLights = ControlGroup("xmasLights", ["xmasTree",
                                               "xmasCowTree",
                                               "xmasBackLights"],
                                               resources=cacheResources,
                                               type="light", group=["Lights", "Xmas"], label="Xmas lights")
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
                                               "poolLights",
                                               "holidayLights",
                                               "xmasTree",
                                               "xmasCowTree",
                                               "xmasBackLights"],
                                               resources=cacheResources,
                                               type="light", group="Lights", label="Outside lights")
    resources.addRes(holidayLights)
    resources.addRes(holiday)
    resources.addRes(porchLights)
    resources.addRes(xmasLights)
    resources.addRes(bedroomLights)
    resources.addRes(outsideLights)

    # Light tasks
    resources.addRes(Task("bedroomLightsOnSunset", SchedTime(event="sunset"), "bedroomLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("bedroomLightsOffSunrise", SchedTime(event="sunrise"), "bedroomLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("porchLightsOnSunset", SchedTime(event="sunset"), "porchLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("outsideLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("outsideLightsOffSunrise", SchedTime(event="sunrise"), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOnSunset", SchedTime(event="sunset"), "xmasLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffSunrise", SchedTime(event="sunrise"), "xmasLights", 0, resources=resources, group="Lights"))
    #        resources.addRes(Task("xmasTreeOnXmas", SchedTime(month=[12], day=[25], hour=[7], minute=[00]), "xmasTree", 1, resources=resources))

    # Schedule
    schedule = Schedule("schedule", tasks=holidayTasks)
    schedule.addTask(resources["bedroomLightsOnSunset"])
    schedule.addTask(resources["bedroomLightsOffSunrise"])
    schedule.addTask(resources["porchLightsOnSunset"])
    schedule.addTask(resources["outsideLightsOffMidnight"])
    schedule.addTask(resources["outsideLightsOffSunrise"])
    schedule.addTask(resources["xmasLightsOnSunset"])
    schedule.addTask(resources["xmasLightsOffMidnight"])
    schedule.addTask(resources["xmasLightsOffSunrise"])
    #        schedule.addTask(resources["xmasTreeOnXmas"])

    restServer = RestServer("holiday", resources, event=stateChangeEvent, label="Holiday lights")

    # Start interfaces
    configData.start()
    neopixelInterface.start()
    temp.start()
    schedule.start()
    restServer.start()
