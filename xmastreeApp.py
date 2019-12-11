
stringLength = 200
darkLength = 46

xmasTreeLabel = "Living room lights"
xmasTreePatternLabel = "Living room light pattern"

defaultConfig = {
    "pattern": "Off",
}

from ha import *
from ha.interfaces.neopixelInterface import *
from ha.interfaces.fileInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *

# dictionary of patterns
patterns = {"On": [Segment(darkLength, stringLength-darkLength, [on], None)],
            "Off": [Segment(darkLength, stringLength-darkLength, [off], None)],
            "White": [Segment(darkLength, stringLength-darkLength, [white], None)],
            "Pink": [Segment(darkLength, stringLength-darkLength, [pink], None)],
            "Red": [Segment(darkLength, stringLength-darkLength, [red], None)],
            "Orange": [Segment(darkLength, stringLength-darkLength, [orange], None)],
            "Yellow": [Segment(darkLength, stringLength-darkLength, [yellow], None)],
            "Green": [Segment(darkLength, stringLength-darkLength, [green], None)],
            "Blue": [Segment(darkLength, stringLength-darkLength, [blue], None)],
            "Purple": [Segment(darkLength, stringLength-darkLength, [purple], None)],
            "Cyan": [Segment(darkLength, stringLength-darkLength, [cyan], None)],
            "Magenta": [Segment(darkLength, stringLength-darkLength, [magenta], None)],
            "Rust": [Segment(darkLength, stringLength-darkLength, [rust], None)],
            "Indigo": [Segment(darkLength, stringLength-darkLength, [indigo], None)],
            "Christmas": [Segment(darkLength, stringLength-darkLength, 3*[red]+3*[green], None)],
            "Christmas color": [Segment(darkLength, stringLength-darkLength, [red]+[green]+[purple]+[blue]+[yellow], None)],
            "Hanukkah": [Segment(darkLength, stringLength-darkLength, 7*[blue]+3*[white], None)],
            "Halloween": [Segment(darkLength, stringLength-darkLength, 5*[orange]+3*[rust]+2*[purple], FlickerAnimation())],
            "Valentines day": [Segment(darkLength, stringLength-darkLength, 1*[white]+2*[pink]+5*[red]+2*[pink], None)],
            "St Patricks day": [Segment(darkLength, stringLength-darkLength, [green], None)],
            "May day": [Segment(darkLength, stringLength-darkLength, [red], None)],
            "Mardi gras": [Segment(darkLength, stringLength-darkLength, 3*[purple]+3*[yellow]+3*[green], SparkleAnimation(rate=5))],
            "Presidents day": [Segment(darkLength, stringLength-darkLength, 3*[red]+3*[white]+3*[blue], None)],
            "4th of July": [Segment(darkLength, stringLength-darkLength, 5*[red]+5*[white]+5*[blue], SparkleAnimation(rate=1))],
            "Bastille day": [Segment(darkLength, stringLength-darkLength, 10*[red]+10*[white]+10*[blue], None)],
            "Cinco de Mayo": [Segment(darkLength, stringLength-darkLength, 10*[green]+10*[white]+10*[red], None)],
            "Easter": [Segment(darkLength, stringLength-darkLength, [yellow]+[blue]+[green]+[cyan]+[magenta], None)],
            "Sweden day": [Segment(darkLength, stringLength-darkLength, 5*[blue]+5*[yellow], None)],
            "Canada day": [Segment(darkLength, stringLength-darkLength, 5*[red]+5*[white], None)],
            "Fall": [Segment(darkLength, stringLength-darkLength, 5*[red]+5*[orange]+5*[rust]+5*[orange], None)],
            "Gay pride": [Segment(darkLength, stringLength-darkLength, [pink]+[red]+[orange]+[yellow]+[green]+[blue]+[purple], SparkleAnimation(rate=3))],
            "Holi": [Segment(darkLength, stringLength-darkLength, [red]+[yellow]+[blue]+[green]+[orange]+[purple]+[pink]+[magenta], None)],
            "Columbus day": [Segment(darkLength, stringLength-darkLength, [green]+[white]+[red], None)],
            "MLK day": [Segment(darkLength, stringLength-darkLength, [white]+[red]+[yellow]+[rust], None)],
            "Spectrum": [Segment(darkLength, stringLength-darkLength, 3*[red]+3*[orange]+3*[yellow]+3*[green]+3*[blue]+3*[purple], CrawlAnimation(rate=1, direction=0))],
            "LRabbit": [Segment(darkLength, stringLength-darkLength, 3*[rust]+3*[red]+3*[orange]+3*[yellow]+3*[white]+3*[yellow]+3*[orange]+3*[red]+3*[rust]+73*[off], CrawlAnimation(rate=1, direction=1))],
            "RRabbit": [Segment(darkLength, stringLength-darkLength, 3*[rust]+3*[red]+3*[orange]+3*[yellow]+3*[white]+3*[yellow]+3*[orange]+3*[red]+3*[rust]+73*[off], CrawlAnimation(rate=1, direction=0))],
            "Random": [Segment(darkLength, stringLength-darkLength, [off], RandomColorAnimation(rate=5))],
            }

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    neopixelInterface = NeopixelInterface("neopixelInterface", None, length=stringLength, event=stateChangeEvent)
    configData = FileInterface("configData", fileName=stateDir+"lights.conf", event=stateChangeEvent, initialState=defaultConfig)

    # Persistent config data
    xmasTreePattern = MultiControl("xmasTreePattern", configData, "pattern", values=sorted(list(patterns.keys())),
                            group=["Lights", "Holiday"], label=xmasTreePatternLabel)

    # Resources
    xmasTree = HolidayLightControl("xmasTree", neopixelInterface, patterns, xmasTreePattern, type="light", group=["Lights", "Holiday"], label=xmasTreeLabel)
    resources = Collection("resources", resources=[xmasTree, xmasTreePattern])
    restServer = RestServer("livingroom", resources, event=stateChangeEvent, label="Living room")

    # Start interfaces
    configData.start()
    neopixelInterface.start()
    restServer.start()
