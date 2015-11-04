from ha.HAClasses import *
from ha.GPIOInterface import *
from ha.I2CInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.restServer import *
from ha.restInterface import *
#from ha.thingInterface import *

#def frontLightSwitch(sensor, state):
#    log(sensor.name, "state:", state)
#    resources["frontLights"].setState(state)
    
if __name__ == "__main__":
    # Resources
    global resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    gpio0 = GPIOInterface("GPIO0", i2c1, addr=0x20, bank=0, inOut=0x00)
    gpio1 = GPIOInterface("GPIO1", i2c1, addr=0x20, bank=1, inOut=0xff, config=[(GPIOInterface.IPOL+1, 0x75)])
    tc74 = TC74Interface("TC74", i2c1)
    temp = TempInterface("Temp", tc74, sample=10)
#    thing = ThingInterface("Thing", event=stateChangeEvent)
    
    # Lights
#    resources.addRes(HAControl("frontLights", gpio0, 0, type="light", group="Lights", label="Front lights"))
#    frontLights = HAControl("backLights", HARestInterface("frontLights", service ="192.168.1.187:7378", cache=False, event=stateChangeEvent), "/resources/frontLight/state", type="light", group="Lights", label="Front lights")
    resources.addRes(HAControl("garageBackDoorLight", gpio0, 1, type="light", group="Lights", label="Garage back door light"))
#    resources.addRes(HASensor("frontLightSwitch", gpio1, 0, type="light", group="Lights", label="Front light switch", interrupt=frontLightSwitch))
#    resources.addRes(HAControl("bedroomLight", thing, type="dimmer", group="Lights", label="Bedroom light"))
#    resources.addRes(HAControl("bathroomLight", thing, type="dimmer", group="Lights", label="Bathroom light"))
#    bedroomLight = HAControl("bedroomLight", HARestInterface("bedroomLight", service ="192.168.1.153:7378", cache=False, event=stateChangeEvent), "/resources/bedroomLight/state", type="dimmer", group="Lights", label="Bedroom light")
#    bathroomLight = HAControl("bathroomLight", HARestInterface("bathroomLight", service ="192.168.1.152:7378", cache=False, event=stateChangeEvent), "/resources/bathroomLight/state", type="dimmer", group="Lights", label="Bathroom light")
#    backLights = HAControl("backLights", HARestInterface("backLights", service ="192.168.1.193:7378", cache=False, event=stateChangeEvent), "/resources/backLights/state", type="light", group="Lights", label="Back lights")
#    resources.addRes(HAControl("testLight", gpio0, 7, type="light", group="Lights", label="TestOutput"))
#    resources.addRes(HASensor("testSwitch", gpio1, 7, type="light", group="Lights", label="Test input"))

    # Doors
    resources.addRes(HASensor("garageBackDoor", gpio1, 1, type="door", group="Doors", label="Garage Back"))
    resources.addRes(HASensor("garageDoor", gpio1, 3, type="door", group="Doors", label="Garage Door"))

    # Water
    resources.addRes(HAControl("recircPump", gpio0, 3, type="hotwater", group="Water", label="Hot water"))

    # Temperature
    resources.addRes(HASensor("garageTemp", temp, 0x4d, group="Temperature", label="Garage temp", type="tempF"))
    
    # Start interfaces
    gpio0.start()
    gpio1.start()
    temp.start()
    restServer = RestServer(resources, event=stateChangeEvent, label="Garage")
    restServer.start()

