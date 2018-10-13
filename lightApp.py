
from ha import *
#from ha.interfaces.gpioInterface import *
#from ha.interfaces.ledInterface import *
from ha.interfaces.neopixelInterface import *
from ha.interfaces.fileInterface import *
from ha.controls.holidayLightControl import *
from ha.rest.restServer import *

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
    holidayLights = HolidayLightControl("holidayLights", neopixelInterface, patternControl=holidayLightPattern, animationControl=holidayLightAnimation,
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

