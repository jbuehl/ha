
stringLength = 200
darkLength = 0

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
patterns = {"On": [Segment(darkLength, stringLength-darkLength, [color(255,255,255)], None)],
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
            "Christmas": [Segment(darkLength, stringLength-darkLength-1, 3*[red]+3*[green], None), Segment(0, 1, [color(255,255,255)])],
            "Christmas color": [Segment(darkLength, stringLength-darkLength-1, [red]+[green]+[purple]+[blue]+[yellow], None), Segment(0, 1, [color(255,255,255)])],
            "Hanukkah": [Segment(darkLength, stringLength-darkLength, 7*[blue]+3*[white], None)],
            "Spectrum": [Segment(darkLength, stringLength-darkLength, 10*[red]+10*[orange]+10*[yellow]+10*[green]+10*[cyan]+10*[blue]+10*[purple]+10*[magenta], CrawlAnimation(rate=10, direction=1))],
            "Rabbit": [Segment(darkLength, stringLength-darkLength, 3*[rust]+3*[red]+3*[orange]+3*[yellow]+3*[green]+3*[cyan]+3*[blue]+3*[purple]+3*[indigo]+173*[off], CrawlAnimation(rate=1, direction=1))],
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
    restServer = RestServer("frontyard", resources, event=stateChangeEvent, label="Front yard")

    # Start interfaces
    configData.start()
    neopixelInterface.start()
    restServer.start()
