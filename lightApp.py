
from ha import *
#from ha.interfaces.gpioInterface import *
#from ha.interfaces.ledInterface import *
from ha.interfaces.neopixelInterface import *
from ha.interfaces.fileInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *

# colors
def color(r, g, b):
    return (r<<16)+(g<<8)+b
    
on = [color(255,255,255)]
off = [color(0,0,0)]

white = [color(255,191,127)]
pink = [color(255,63,63)]
red = [color(255,0,0)]
orange = [color(255,63,0)]
yellow = [color(255,127,0)]
green = [color(0,255,0)]
blue = [color(0,0,127)]
purple = [color(63,0,63)]
cyan = [color(0,255,255)]
magenta = [color(255,0,63)]
rust = [color(63,7,0)]

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

# animation types
animations = {"solid": [0],             # type 
              "rcrawl": [1, 3, 1],      # type, rate, direction
              "lcrawl": [1, 3, -1],     # type, rate, direction
              "sparkle": [2, 3, .7],    # type, rate, factor
              "flicker": [3, 1, .7],    # type, rate, factor
              "blink": [4, 15],         # type, rate
              "fade": [5, 6],           # type, rate
              }

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
#    gpioInterface = GPIOInterface("gpioInterface", event=stateChangeEvent)
#    ledInterface = LedInterface("ledInterface", gpioInterface)
    neopixelInterface = NeopixelInterface("neopixelInterface", None, length=343)
    configData = FileInterface("configData", fileName=stateDir+"lights.conf", event=stateChangeEvent)
    
    # Lights
#    sculptureLights = Control("sculptureLights", ledInterface, 18, type="led", group="Lights", label="Sculpture light")
    holidayLightPattern = Control("holidayLightPattern", configData, "pattern", group="Lights", label="Holiday light pattern")
    holidayLightAnimation = Control("holidayLightAnimation", configData, "animation", group="Lights", label="Holiday light animation")
    holidayLights = HolidayLightControl("holidayLights", neopixelInterface, patterns, animations, 
                                        patternControl=holidayLightPattern, animationControl=holidayLightAnimation,
                                        segments=[Segment("left", neopixelInterface,   0, 112, patterns["orange"], animations["fade"]),
                                                  Segment("center", neopixelInterface, 112,  58, patterns["halloween"], animations["flicker"]),
                                                  Segment("right", neopixelInterface, 170, 173, patterns["orange"], animations["fade"]),
                                                 ],
                                        type="light", group="Lights", label="Holiday lights")

    # Resources
    resources = Collection("resources", resources=[holidayLights, holidayLightPattern, holidayLightAnimation,
#                                                   sculptureLights, 
                                                   ])
    restServer = RestServer("lights", resources, event=stateChangeEvent, label="Lights")

    # Start interfaces
#    gpioInterface.start()
    configData.start()
    if not holidayLightPattern.getState():
        holidayLightPattern.setState(holidayLightPatternDefault)
    if not holidayLightAnimation.getState():
        holidayLightAnimation.setState(holidayLightAnimationDefault)
    neopixelInterface.start()
    restServer.start()

