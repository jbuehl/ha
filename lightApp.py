
from ha import *
#from ha.interfaces.gpioInterface import *
#from ha.interfaces.ledInterface import *
from ha.interfaces.neopixelInterface import *
#from ha.interfaces.fileInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *

# dictionary of patterns
patterns = {"on": on,
            "off": off,
            "white": white,
            "pink": pink,
            "red": red,
            "orange": orange,
            "yellow": yellow,
            "green": green,
            "blue": blue,
            "purple": purple,
            "cyan": cyan,
            "magenta": magenta,
            "rust": rust,
            "xmas": 3*red+3*green,
            "hanukkah": 3*blue+3*white,
            "halloween": 5*orange+3*rust+2*purple,
            "valentines": white+pink+red+pink,
            "stpatricks": green,
            "mardigras": 3*purple+3*yellow+3*green,
            "july": 3*red+3*white+3*blue,
            "cincodemayo": green+white+red,
            "easter": yellow+blue+green+cyan+magenta,
            "sweden": blue+yellow,
            "fall": red+orange+rust+orange,
            "pride": pink+red+orange+yellow+green+blue+purple,
            "holi": red+yellow+blue+green+orange+purple+pink+magenta,
            "mayday": red,
            "columbus": green+white+red,
            "mlk": white+red+yellow+rust,
            }

# more colors
c1 = color(255,000,000)
c2 = color(191,063,000)
c3 = color(127,127,000)
c4 = color(063,191,000)
c5 = color(000,255,000)
c6 = color(000,191,063)
c7 = color(000,127,127)
c8 = color(000,063,191)
c9 = color(000,000,255)
c10 = color(063,000,191)
c11 = color(127,000,127)
c12 = color(191,000,063)
c13 = color(223,000,031)

# strings
leftString = 112
centerString = 58
rightString1 = 30
rightString2 = 143

# create a spectral pattern
def spectrum(incr=1):
    # incr ideally should be a power of 2, but can be any positive integer < 256
    # pattern length will be 3*256/incr
    (r, g, b) = (255, -1, -1)
    cycle = 256 / incr
    pattern = []
    for pixel in range(cycle):
        pattern.append(color(r, g, b))
        r -= incr
        g += incr
    for pixel in range(cycle):
        pattern.append(color(r, g, b))
        g -= incr
        b += incr
    for pixel in range(cycle):
        pattern.append(color(r, g, b))
        b -= incr
        r += incr
    return pattern

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
#    gpioInterface = GPIOInterface("gpioInterface", event=stateChangeEvent)
#    ledInterface = LedInterface("ledInterface", gpioInterface)
    neopixelInterface = NeopixelInterface("neopixelInterface", None, length=550, event=stateChangeEvent)
#    configData = FileInterface("configData", fileName=stateDir+"lights.conf", event=stateChangeEvent)
    
    # Lights
#    sculptureLights = Control("sculptureLights", ledInterface, 18, type="led", group="Lights", label="Sculpture light")
#    holidayLightPattern = Control("holidayLightPattern", configData, "pattern", group="Lights", label="Holiday light pattern")
#    holidayLightAnimation = Control("holidayLightAnimation", configData, "animation", group="Lights", label="Holiday light animation")
    leftSegment = ("leftSegment", 0, 112)
    centerSegment = ("centerSegment", 112, 58)
    rightSegment = ("rightSegment", 170, 173)
    allLights = ("allLights", 0, 343)
    
    fallLights = HolidayLightControl("fallLights", neopixelInterface, 
                                        segments=[Segment("all",     0, 343, 
                                                          pattern=5*[red]+5*[orange]+5*[rust]+5*[orange]),
                                                 ],
                                        type="light", group="Lights", label="Fall lights")
    halloweenLights = HolidayLightControl("halloweenLights", neopixelInterface, 
#                                        patterns, animations, 
#                                        patternControl=holidayLightPattern, animationControl=holidayLightAnimation,
                                        segments=[Segment("leftSegment",     0, 112, 
                                                           pattern=5*[orange]),
                                                  Segment("centerSegment", 112,  58, 
                                                           pattern=2*[indigo]),
                                                  Segment("rightSegment",  170, 140, 
                                                           pattern=5*[orange], 
                                                           animation=FlickerAnimation(rate=3)),
                                                  Segment("farRightSegment", 310, 33, 
                                                           pattern=5*[orange], 
                                                           animation=FlickerAnimation()),
                                                 ],
                                        type="light", group="Lights", label="Halloween lights")
    hanukkahLights = HolidayLightControl("hanukkahLights", neopixelInterface, 
                                        segments=[Segment("leftSegment",     0, 200, 
                                                           pattern=7*[blue]+3*[white]),
                                                  Segment("darkSegment", 200,  200, 
                                                           pattern=[off]),
                                                  Segment("rightSegment",  400, 143, 
                                                           pattern=7*[blue]+3*[white]),
                                                 ],
                                        type="light", group="Lights", label="Hanukkah lights")
#    christmasPattern = 3*[red]+1*[white]+6*[green]
    christmasPattern = 1*[green]+1*[magenta]+1*[blue]+1*[yellow]+1*[red]
    christmasAnimation = SparkleAnimation(rate=15, factor=.1)
#    treeUpPattern = 5*[c1]+5*[c2]+5*[c3]+5*[c4]+5*[c5]+5*[c6]+5*[c7]+5*[c8]+5*[c9]+5*[c10]+5*[c11]+5*[c12]+5*[c13]
#    treeDownPattern = 1*[c13]+1*[c12]+1*[c11]+1*[c10]+1*[c9]+1*[c8]+1*[c7]+1*[c6]+1*[c5]+1*[c4]+1*[c3]+1*[c2]+1*[c1]
#    treeUpPattern = 1*[red]+1*[white]+1*[green]
    treeUpPattern = [white]
    treeDownPattern = treeUpPattern
    spectrum4Pattern = spectrum(4)
#    treeUpAnimation = CrawlAnimation(direction=1, rate=5)
#    treeDownAnimation = CrawlAnimation(direction=-1, rate=25)
    treeUpAnimation = SparkleAnimation(rate=15, factor=.1)
    treeDownAnimation = treeUpAnimation
    starPattern = [white]
    starAnimation = None
    windowPattern = 1*[red]+1*[white]+1*[green]
    windowAnimation = None
    treeSegments = [  Segment("treeSegment", 303,  65, pattern=treeUpPattern,animation=treeUpAnimation),
                      Segment("starSegment", 368,  4, pattern=starPattern, animation=starAnimation),
                      Segment("treeSegment", 372,  13, pattern=treeDownPattern,animation=treeDownAnimation),
                    ]
    insideSegments = [Segment("windowSegment", 200,  100, pattern=windowPattern, animation=windowAnimation),
                      Segment("darkSegment", 300,  3,pattern=[off])] + \
                      treeSegments + \
                     [Segment("darkSegment", 385,  3,pattern=[off]),
                      Segment("windowSegment", 388,  12, pattern=windowPattern, animation=windowAnimation)]
    christmasLights = HolidayLightControl("christmasLights", neopixelInterface, 
                                        segments=[Segment("leftSegment",     0, 200, 
                                                           pattern=spectrum4Pattern[-8:]+spectrum4Pattern, 
                                                           animation=christmasAnimation)] + \
                                                  insideSegments + \
                                                 [Segment("rightSegment",  400, 143, 
                                                           pattern=spectrum4Pattern, 
                                                           animation=christmasAnimation)],
                                        type="light", group="Lights", label="Christmas lights")
    christmasTree = HolidayLightControl("christmasTree", neopixelInterface, 
                                        segments=[Segment("darkSegment", 0,  303, 
                                                           pattern=[off])] + \
                                                  treeSegments,
                                        type="light", group="Lights", label="Christmas tree")
    electionLights = HolidayLightControl("electionLights", neopixelInterface, 
                                        segments=[Segment("leftSegment",     0, 112, 
                                                           pattern=10*[red]+10*[white]+10*[blue], 
                                                           animation=CrawlAnimation(direction=1)),
                                                  Segment("centerSegment", 112,  58, 
                                                           pattern=1*[red]+1*[white]+1*[blue], 
                                                           animation=SparkleAnimation(rate=1)),
                                                  Segment("rightSegment",  170, 173, 
                                                           pattern=10*[red]+10*[white]+10*[blue], 
                                                           animation=CrawlAnimation(direction=-1)),
                                                 ],
                                        type="light", group="Lights", label="Election lights")
    testLights = HolidayLightControl("testLights", neopixelInterface, 
                                        segments=[Segment("all",     0, 200, 
                                                           pattern=spectrum(4), 
                                                           animation=CrawlAnimation(direction=1)),
                                                  Segment("all",     0, 200, 
                                                           pattern=spectrum(4), 
                                                           animation=CrawlAnimation(direction=1)),
                                                  Segment("all",     0, 150, 
                                                           pattern=spectrum(4), 
                                                           animation=CrawlAnimation(direction=1)),
                                                 ],
                                        type="light", group="Lights", label="Test lights")

    # Resources
    resources = Collection("resources", resources=[fallLights, halloweenLights, hanukkahLights, christmasLights, christmasTree, electionLights, testLights,
#                                                   holidayLightPattern, holidayLightAnimation,
#                                                   sculptureLights, 
                                                   ])
    restServer = RestServer("lights", resources, event=stateChangeEvent, label="Lights")

    # Start interfaces
#    gpioInterface.start()
#    configData.start()
#    if not holidayLightPattern.getState():
#        holidayLightPattern.setState(holidayLightPatternDefault)
#    if not holidayLightAnimation.getState():
#        holidayLightAnimation.setState(holidayLightAnimationDefault)
    neopixelInterface.start()
    restServer.start()

