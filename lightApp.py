
from ha import *
#from ha.interfaces.gpioInterface import *
#from ha.interfaces.ledInterface import *
from ha.interfaces.holidayLightInterface import *
from ha.rest.restServer import *

stateChangeEvent = threading.Event()

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
#    gpioInterface = GPIOInterface("gpioInterface", event=stateChangeEvent)
#    ledInterface = LedInterface("ledInterface", gpioInterface)
    holidayLightInterface = HolidayLightInterface("holidayLightInterface", None, length=292, repeat=5)
    
    # Lights
#    sculptureLights = Control("sculptureLights", ledInterface, 18, type="led", group="Lights", label="Sculpture light")
    holidayLights = Control("holidayLights", holidayLightInterface, "state", type="light", group="Lights", label="Holiday lights")
    holidayLightPattern = Control("holidayLightPattern", holidayLightInterface, "pattern")
    holidayLightAnimation = Control("holidayLightAnimation", holidayLightInterface, "animation")

    # Resources
    resources = Collection("resources", resources=[
#                                                   sculptureLights, 
                                                   holidayLights, holidayLightPattern, holidayLightAnimation,
                                                   ])
    restServer = RestServer("lights", resources, event=stateChangeEvent, label="Lights")

    # Start interfaces
#    gpioInterface.start()
    holidayLightInterface.start()
    restServer.start()

