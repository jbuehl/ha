
stringLength = 343
darkLength = 0
farLeftLength = 12
cameraLength = 10
leftLength = 90
centerLength = 58
rightLength = 140
farRightLength = 33

defaultConfig = {
    "holiday": "None",
}

from ha import *
from ha.interfaces.neopixelInterface import *
from ha.interfaces.fileInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *

# dictionary of patterns
patterns = {"On": [Segment(0, stringLength, [on], None)],
            "Off": [Segment(0, stringLength, [off], None)],
            "White": [Segment(0, stringLength, [white], None)],
            "Pink": [Segment(0, stringLength, [pink], None)],
            "Red": [Segment(0, stringLength, [red], None)],
            "Orange": [Segment(0, stringLength, [orange], None)],
            "Yellow": [Segment(0, stringLength, [yellow], None)],
            "Green": [Segment(0, stringLength, [green], None)],
            "Blue": [Segment(0, stringLength, [blue], None)],
            "Purple": [Segment(0, stringLength, [purple], None)],
            "Cyan": [Segment(0, stringLength, [cyan], None)],
            "Magenta": [Segment(0, stringLength, [magenta], None)],
            "Rust": [Segment(0, stringLength, [rust], None)],
            "Indigo": [Segment(0, stringLength, [indigo], None)],
            "Christmas": [Segment(0, farLeftLength, 4*[green]+4*[white]+4*[red], None),
                          Segment(0, cameraLength, [off], None),
                          Segment(0, leftLength, 4*[green]+4*[white]+4*[red], None),
                          Segment(0, centerLength, [white], None),
                          Segment(0, rightLength+farRightLength, 4*[green]+4*[white]+4*[red], None),
                         ],
            "Christmas sparkle": [Segment(0, farLeftLength, 5*[green]+2*[white]+5*[red], CrawlAnimation(direction=1)),
                          Segment(0, cameraLength, [off], None),
                          Segment(0, leftLength, 5*[green]+2*[white]+5*[red], CrawlAnimation(direction=1)),
                          Segment(0, centerLength, [white], SparkleAnimation(rate=2, factor=.7)),
                          Segment(0, rightLength+farRightLength, 5*[green]+2*[white]+5*[red], CrawlAnimation(direction=0)),
                         ],
            "New years eve": [Segment(0, farLeftLength, 2*[red]+2*[yellow]+2*[green]+2*[orange]+2*[blue]+2*[white], SparkleAnimation(rate=1, factor=.7)),
                          Segment(0, cameraLength, [off], None),
                          Segment(0, leftLength, 2*[red]+2*[yellow]+2*[green]+2*[orange]+2*[blue]+2*[white], SparkleAnimation(rate=1, factor=.7)),
                          Segment(0, centerLength, [white], SparkleAnimation(rate=1, factor=.7)),
                          Segment(0, rightLength+farRightLength, 2*[red]+2*[yellow]+2*[green]+2*[orange]+2*[blue]+2*[white], SparkleAnimation(rate=2, factor=.7)),
                         ],
            "Hanukkah": [Segment(0, stringLength, 7*[blue]+3*[white], None)],
            "Halloween": [Segment(0, stringLength, 5*[orange]+3*[rust]+2*[purple], FlickerAnimation())],
            "Spooky":    [Segment(0, farLeftLength, [orange], None),
                          Segment(0, cameraLength, [off], None),
                          Segment(0, leftLength, 5*[orange]+3*[rust]+2*[purple], None),
                          Segment(0, centerLength, [orange], None),
                          Segment(0, rightLength, 5*[orange]+3*[rust]+2*[purple], FlickerAnimation(rate=1)),
                          Segment(0, farRightLength, 5*[orange]+3*[rust]+2*[purple], FlickerAnimation()),
                         ],
            "Election day": [Segment(0, farLeftLength, 10*[red]+10*[white]+10*[blue], None),
                             Segment(0, cameraLength, [off], None),
                             Segment(0, leftLength, 10*[red]+10*[white]+10*[blue], CrawlAnimation(direction=1)),
                             Segment(0, centerLength, [white], SparkleAnimation(rate=1)),
                             Segment(0, rightLength+farRightLength, 10*[red]+10*[white]+10*[blue], CrawlAnimation(direction=0)),
                            ],
            "Valentines day": [Segment(0, stringLength, 1*[white]+2*[pink]+5*[red]+2*[pink], None)],
            "St Patricks day": [Segment(0, stringLength, [green], None)],
            "May day": [Segment(0, stringLength, [red], None)],
            "Mardi gras": [Segment(0, stringLength, 3*[purple]+3*[yellow]+3*[green], SparkleAnimation(rate=5))],
            "Presidents day": [Segment(0, stringLength, 3*[red]+3*[white]+3*[blue], None)],
            "4th of July": [Segment(0, stringLength, 5*[red]+5*[white]+5*[blue], SparkleAnimation(rate=1))],
            "Bastille day": [Segment(0, stringLength, 10*[red]+10*[white]+10*[blue], None)],
            "Cinco de Mayo": [Segment(0, stringLength, 10*[green]+10*[white]+10*[red], None)],
            "Easter": [Segment(0, stringLength, [yellow]+[blue]+[green]+[cyan]+[magenta], None)],
            "Sweden day": [Segment(0, stringLength, 5*[blue]+5*[yellow], None)],
            "Canada day": [Segment(0, stringLength, 5*[red]+5*[white], None)],
            "Fall": [Segment(0, stringLength, 5*[red]+5*[orange]+5*[rust]+5*[orange], None)],
            "Gay pride": [Segment(0, stringLength, [pink]+[red]+[orange]+[yellow]+[green]+[blue]+[purple], SparkleAnimation(rate=3))],
            "Holi": [Segment(0, stringLength, [red]+[yellow]+[blue]+[green]+[orange]+[purple]+[pink]+[magenta], None)],
            "Columbus day": [Segment(0, stringLength, [green]+[white]+[red], None)],
            "MLK day": [Segment(0, stringLength, [white]+[red]+[yellow]+[rust], None)],
            "Spectrum": [Segment(0, stringLength, [red]+[orange]+[yellow]+[green]+[blue]+[purple], CrawlAnimation(direction=1))],
            "Rabbit": [Segment(0, stringLength, 3*[rust]+3*[red]+3*[orange]+3*[yellow]+3*[white]+3*[yellow]+3*[orange]+3*[red]+3*[rust]+73*[off], CrawlAnimation(rate=1))],
            "Random": [Segment(0, stringLength, [off], RandomColorAnimation(rate=5))],
            }

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    neopixelInterface = NeopixelInterface("neopixelInterface", None, length=stringLength, event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"lights.conf", event=stateChangeEvent, initialState=defaultConfig)

    # Persistent config data
    holiday = MultiControl("holiday", configData, "holiday", values=sorted(list(patterns.keys())),
                            group=["Lights", "Holiday"], label="Holiday")

    holidayLights = HolidayLightControl("holidayLights", neopixelInterface, patterns, holiday, type="light", group=["Lights", "Holiday"], label="Holiday lights")

# Tasks
    # 2019
    holidayTasks = [
        Task("offTask",              SchedTime(                              hour=12, minute=0), holiday, "Off"),
        Task("valentinesTask",       SchedTime(year=2020, month=Feb, day=14, hour=12, minute=0), holiday, "Valentines day"),
        Task("presidentsTask",       SchedTime(year=2020, month=Feb, day=17, hour=12, minute=0), holiday, "Presidents day"),
        Task("mardigrasTask",        SchedTime(year=2020, month=Feb, day=[22,23,24,25],  hour=12, minute=0), holiday, "Mardi gras"),
        Task("stpatricksTask",       SchedTime(year=2020, month=Mar, day=17, hour=12, minute=0), holiday, "St Patricks day"),
        Task("easterTask",           SchedTime(year=2020, month=Apr, day=[11,12], hour=12, minute=0), holiday, "Easter"),
        Task("maydayTask",           SchedTime(year=2020, month=May, day=1,  hour=12, minute=0), holiday, "May day"),
        Task("cincodemayoTask",      SchedTime(year=2020, month=May, day=5,  hour=12, minute=0), holiday, "Cinco de Mayo"),
        Task("swedenTask",           SchedTime(year=2020, month=Jun, day=6,  hour=12, minute=0), holiday, "Sweden day"),
        Task("prideTask",            SchedTime(year=2020, month=Jun, day=12, hour=12, minute=0), holiday, "Pride day"),
        Task("flagTask",             SchedTime(year=2020, month=Jun, day=14, hour=12, minute=0), holiday, "Flag day"),
        Task("canadaTask",           SchedTime(year=2020, month=Jul, day=1,  hour=12, minute=0), holiday, "Canada day"),
        Task("july3Task",            SchedTime(year=2020, month=Jul, day=3,  hour=12, minute=0), holiday, "Presidents day"),
        Task("july4Task",            SchedTime(year=2020, month=Jul, day=4,  hour=12, minute=0), holiday, "4th of July"),
        Task("bastilleTask",         SchedTime(year=2020, month=Jul, day=14, hour=12, minute=0), holiday, "Bastille day"),
        Task("fallTask",             SchedTime(year=2020, month=Sep, day=21, hour=12, minute=0), holiday, "Fall"),
        Task("halloweenTask",        SchedTime(year=2020, month=Oct, day=[25,26,27,28,29,30], hour=12, minute=0), holiday, "Halloween"),
        Task("spookyTask",           SchedTime(year=2020, month=Oct, day=31, hour=12, minute=0), holiday, "Spooky"),
        Task("electionTask",         SchedTime(year=2020, month=Nov, day=3,  hour=12, minute=0), holiday, "Election day"),
        Task("thanksgivingTask",     SchedTime(year=2020, month=Nov, day=26, hour=12, minute=0), holiday, "Fall"),
        Task("christmasTask",        SchedTime(year=2020, month=Dec,         hour=12, minute=0), holiday, "Christmas"),
        Task("hanukkahTask",         SchedTime(year=2020, month=Dec, day=11, hour=12, minute=0), holiday, "Hanukkah"),
        Task("christmasSparkleTask", SchedTime(year=2020, month=Dec, day=[24,25], hour=12, minute=0), holiday, "Christmas sparkle"),
        Task("newYearsEveTask",      SchedTime(year=2020, month=Dec, day=31, hour=12, minute=0), holiday, "New years eve"),
        ]

    # Schedule
    schedule = Schedule("schedule", tasks=holidayTasks)

    # Resources
    resources = Collection("resources", resources=[holidayLights, holiday])
    restServer = RestServer("holiday", resources, event=stateChangeEvent, label="Holiday lights")

    # Start interfaces
    configData.start()
    neopixelInterface.start()
    schedule.start()
    restServer.start()
