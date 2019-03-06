
stringLength = 343
holidayLightDefault = "offLights"

from ha import *
from ha.interfaces.neopixelInterface import *
from ha.interfaces.fileInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *

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
            "mardigrasPattern": 3*[purple]+3*[yellow]+3*[green],
            "presidentsPattern": 3*[red]+3*[white]+3*[blue],
            "july4Pattern": 5*[red]+5*[white]+5*[blue],
            "bastillePattern": 10*[red]+10*[white]+10*[blue],
            "cincodemayoPattern": 10*[green]+10*[white]+10*[red],
            "easterPattern": [yellow]+[blue]+[green]+[cyan]+[magenta],
            "swedenPattern": 5*[blue]+5*[yellow],
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
    configData = FileInterface("configData", fileName=stateDir+"lights.conf", event=stateChangeEvent)

    # Persistent config data
    holiday = Control("holiday", configData, "holiday", group=["Lights", "Holiday"], label="Holiday")

    # Light controls
#    leftSegment = ("leftSegment", 0, 112)
#    centerSegment = ("centerSegment", 112, 58)
#    rightSegment = ("rightSegment", 170, 173)
#    allLights = ("allLights", 0, 343)

    offLights = HolidayLightControl("offLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                          pattern=patterns["offPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Off")
    valentinesLights = HolidayLightControl("valentinesLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["valentinesPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Valentines day")
    mardigrasLights = HolidayLightControl("mardigrasLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["mardigrasPattern"],
                                                           animation=SparkleAnimation(rate=5))],
                                        type="light", group=["Lights", "Holiday"], label="Mardi gras")
    presidentsLights = HolidayLightControl("presidentsLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["presidentsPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Presidents day")
    stpatricksLights = HolidayLightControl("stpatricksLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["stpatricksPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="St Patricks day")
    easterLights = HolidayLightControl("easterLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["easterPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Easter")
    cincodemayoLights = HolidayLightControl("cincodemayoLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["cincodemayoPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Cinco de mayo")
    swedenLights = HolidayLightControl("swedenLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["swedenPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Sweden day")
    flagLights = HolidayLightControl("flagLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["presidentsPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Flag day")
    july4Lights = HolidayLightControl("july4Lights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["july4Pattern"],
                                                           animation=SparkleAnimation(rate=1))],
                                        type="light", group=["Lights", "Holiday"], label="4th of july")
    bastilleLights = HolidayLightControl("bastilleLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["bastillePattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Bastille day")
    fallLights = HolidayLightControl("fallLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                          pattern=patterns["fallPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Fall")
    halloweenLights = HolidayLightControl("halloweenLights", neopixelInterface,
                                        segments=[Segment("leftSegment",     0, 112,
                                                           pattern=5*[orange]),
                                                  Segment("centerSegment", 112,  58,
                                                           pattern=2*[indigo]),
                                                  Segment("rightSegment",  170, 140,
                                                           pattern=5*[orange],
                                                           animation=FlickerAnimation(rate=3)),
                                                  Segment("farRightSegment", 310, 33,
                                                           pattern=5*[orange],
                                                           animation=FlickerAnimation())],
                                        type="light", group=["Lights", "Holiday"], label="Halloween")
    electionLights = HolidayLightControl("electionLights", neopixelInterface,
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
    christmasLights = HolidayLightControl("christmasLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["christmasPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Christmas")
    hanukkahLights = HolidayLightControl("hanukkahLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["hanukkahPattern"])],
                                        type="light", group=["Lights", "Holiday"], label="Hanukkah")
    testLights = HolidayLightControl("testLights", neopixelInterface,
                                        segments=[Segment("all",     0, stringLength,
                                                           pattern=patterns["spectrumPattern"],
                                                           animation=CrawlAnimation(direction=1))],
                                        type="light", group=["Lights", "Holiday"], label="Test")
    # Tasks
    # 2019
    tasks = [
            Task("OffTask",          SchedTime(                              hour=12, minute=00), holiday, "offLights"),
            Task("valentinesTask",   SchedTime(year=2019, month=Feb, day=[13,14], hour=12, minute=0), holiday, "valentinesLights"),
            Task("presidentsTask",   SchedTime(year=2019, month=Feb, day=18, hour=12, minute=0), holiday, "presidentsLights"),
            Task("mardigrasTask",    SchedTime(year=2019, month=Mar, day=[2,3,4,5],  hour=12, minute=0), holiday, "mardigrasLights"),
            Task("stpatricksTask",   SchedTime(year=2019, month=Mar, day=[16,17], hour=12, minute=0), holiday, "stpatricksLights"),
            Task("easterTask",       SchedTime(year=2019, month=Apr, day=[20,21], hour=12, minute=0), holiday, "easterLights"),
            Task("cincodemayoTask",  SchedTime(year=2019, month=May, day=5,  hour=12, minute=0), holiday, "cincodemayoLights"),
            Task("swedenTask",       SchedTime(year=2019, month=Jun, day=6,  hour=12, minute=0), holiday, "swedenLights"),
            Task("flagTask",         SchedTime(year=2019, month=Jun, day=14,  hour=12, minute=0), holiday, "flagLights"),
            Task("july4Task",        SchedTime(year=2019, month=Jul, day=[3,4],  hour=12, minute=0), holiday, "july4Lights"),
            Task("bastilleTask",     SchedTime(year=2019, month=Jul, day=14,  hour=12, minute=0), holiday, "bastilleLights"),
            Task("fallTask",         SchedTime(year=2019, month=Sep, day=21, hour=12, minute=0), holiday, "fallLights"),
            Task("halloweenTask",    SchedTime(year=2019, month=Oct, day=31, hour=12, minute=0), holiday, "halloweenLights"),
            Task("thanksgivingTask", SchedTime(year=2019, month=Nov, day=28, hour=12, minute=0), holiday, "fallLights"),
            Task("christmasTask",    SchedTime(year=2019, month=Dec,         hour=12, minute=0), holiday, "christmasLights"),
            Task("hanukkahTask",     SchedTime(year=2019, month=Dec, day=22, hour=12, minute=0), holiday, "hanukkahLights"),
            ]

    # Schedule
    schedule = Schedule("schedule", tasks=tasks)

    # Resources
    resources = Collection("resources", resources=[valentinesLights, mardigrasLights, presidentsLights, stpatricksLights,
                                                   easterLights, cincodemayoLights, swedenLights, july4Lights, bastilleLights,
                                                   fallLights, halloweenLights, electionLights, christmasLights, hanukkahLights,
                                                   testLights, offLights, holiday
                                                   ])
    holidayLights = AliasControl("holidayLights", None, resources, holiday, type="light", group=["Lights", "Holiday"], label="Holiday lights")
    resources.addRes(holidayLights)
    restServer = RestServer("lights", resources, event=stateChangeEvent, label="Lights")

    # Start interfaces
    configData.start()
    if not holiday.getState():
        holiday.setState(holidayLightDefault)
    neopixelInterface.start()
    schedule.start()
    restServer.start()
