
stringLength = 200

xmasTreeLabel = "Front yard lights"
xmasTreePatternLabel = "Front yard light pattern"

defaultConfig = {
    "pattern": "Off",
}

from ha import *
from ha.interfaces.neopixelInterface import *
from ha.interfaces.fileInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *

# dictionary of patterns
patterns = {"On": [Segment(0, stringLength, [color(255,255,255)], None)],
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
            "Christmas": [Segment(0, stringLength-1, 3*[red]+3*[green], None), Segment(0, 1, [color(255,255,255)])],
            "Christmas color": [Segment(0, stringLength-1, [red]+[green]+[purple]+[blue]+[yellow], None), Segment(0, 1, [color(255,255,255)])],
            "Christmas sparkle": [Segment(0, stringLength, [red]+[green]+[white], SparkleAnimation(rate=2, factor=.7))],
            "Hanukkah": [Segment(0, stringLength, 7*[blue]+3*[white], None)],
            "Spectrum": [Segment(0, stringLength, 10*[red]+10*[orange]+10*[yellow]+10*[green]+10*[cyan]+10*[blue]+10*[purple]+10*[magenta], CrawlAnimation(rate=10, direction=1))],
            "Rabbit": [Segment(0, stringLength, 3*[rust]+3*[red]+3*[orange]+3*[yellow]+3*[green]+3*[cyan]+3*[blue]+3*[purple]+3*[indigo]+173*[off], CrawlAnimation(rate=1, direction=1))],
            "Random": [Segment(0, stringLength, [off], RandomColorAnimation(rate=5))],
            "Sparkle": [Segment(0, stringLength, [color(255,255,255)], SparkleAnimation(rate=1, factor=.7))],
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
    restServer = RestServer("frontyard", resources, event=stateChangeEvent, label="Front yard")

    # Start interfaces
    configData.start()
    neopixelInterface.start()
    restServer.start()
