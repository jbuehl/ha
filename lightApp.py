
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

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
#    gpioInterface = GPIOInterface("gpioInterface", event=stateChangeEvent)
#    ledInterface = LedInterface("ledInterface", gpioInterface)
    neopixelInterface = NeopixelInterface("neopixelInterface", None, length=343)
#    configData = FileInterface("configData", fileName=stateDir+"lights.conf", event=stateChangeEvent)
    
    # Lights
#    sculptureLights = Control("sculptureLights", ledInterface, 18, type="led", group="Lights", label="Sculpture light")
#    holidayLightPattern = Control("holidayLightPattern", configData, "pattern", group="Lights", label="Holiday light pattern")
#    holidayLightAnimation = Control("holidayLightAnimation", configData, "animation", group="Lights", label="Holiday light animation")
    halloweenLights = HolidayLightControl("halloweenLights", neopixelInterface, 
#                                        patterns, animations, 
#                                        patternControl=holidayLightPattern, animationControl=holidayLightAnimation,
                                        segments=[Segment("leftSegment",     0, 112, 5*[orange], FadeAnimation()),
                                                  Segment("centerSegment", 112,  58, 5*[orange]+3*[rust]+2*[purple], FlickerAnimation()),
                                                  Segment("rightSegment",  170, 173, 5*[orange], FadeAnimation()),
                                                 ],
                                        type="light", group="Lights", label="Halloween lights")
    hanukkahLights = HolidayLightControl("hanukkahLights", neopixelInterface, 
                                        segments=[Segment("leftSegment",     0, 112, 5*[blue]+5*[white]),
                                                  Segment("centerSegment", 112,  58, 5*[white]),
                                                  Segment("rightSegment",  170, 173, 5*[blue]+5*[white]),
                                                 ],
                                        type="light", group="Lights", label="Hanukkah lights")
    christmasLights = HolidayLightControl("christmasLights", neopixelInterface, 
                                        segments=[Segment("leftSegment",     0, 112, 3*[red]+3*[green]),
                                                  Segment("centerSegment", 112,  58, 5*[white], SparkleAnimation()),
                                                  Segment("rightSegment",  170, 173, 3*[red]+3*[green]),
                                                 ],
                                        type="light", group="Lights", label="Christmas lights")

    # Resources
    resources = Collection("resources", resources=[halloweenLights, hanukkahLights, christmasLights,
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

