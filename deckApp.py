from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.shadeInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.bmp085Interface import *
from ha.interfaces.hih6130Interface import *
from ha.interfaces.tempInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":

    # Interfaces
    stateChangeEvent = threading.Event()
    gpioInterface = GPIOInterface("gpioInterface", event=stateChangeEvent)
    shadeInterface = ShadeInterface("shadeInterface", gpioInterface)
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    barometer = BMP085Interface("bmp085Interface", i2c1)
    humidity = HIH6130Interface("hih6130Interface", i2c1)
    barometerCache = TempInterface("barometerCache", barometer, sample=10)
    humidityCache = TempInterface("humidityCache", humidity, sample=10)
    
    # Controls
    shade1 = Control("shade1", shadeInterface, 0, type="shade", group="Shades", label="Shade 1")
    shade2 = Control("shade2", shadeInterface, 1, type="shade", group="Shades", label="Shade 2")
    shade3 = Control("shade3", shadeInterface, 2, type="shade", group="Shades", label="Shade 3")
    shade4 = Control("shade4", shadeInterface, 3, type="shade", group="Shades", label="Shade 4")
    allShades = ControlGroup("allShades", [shade1, shade2, shade3, shade4], type="shade", group="Shades", label="All shades")

    # Sensors
    deckTemp = Sensor("deckTemp", barometerCache, "temp", group=["Temperature", "Weather"], label="Deck temp", type="tempF")
    barometer = Sensor("barometer", barometerCache, "barometer", group="Weather", label="Barometer", type="barometer")
    humidity = Sensor("humidity", humidityCache, "humidity", group="Weather", label="Humidity", type="humidity")
    dewpoint = Sensor("dewpoint", humidityCache, "dewpoint", group="Weather", label="Dewpoint", type="tempF")

    # Schedules
    shadesDown = Task("shadesDown", SchedTime(hour=[13], minute=[00], month=[Apr, May, Jun, Jul, Aug, Sep]), allShades, 1, enabled=True)
    shadesUpAprSep = Task("shadesUpAprSep", SchedTime(minute=-30, event="sunset", month=[Apr, Sep]), allShades, 0, enabled=True)
    shadesUpMayAug = Task("shadesUpMayAug", SchedTime(minute=-35, event="sunset", month=[May, Aug]), allShades, 0, enabled=True)
    shadesUpJunJul = Task("shadesUpJunJul", SchedTime(minute=-40, event="sunset", month=[Jun, Jul]), allShades, 0, enabled=True)
    schedule = Schedule("schedule", tasks=[shadesDown, shadesUpAprSep, shadesUpMayAug, shadesUpJunJul])

    # Resources
    resources = Collection("resources", resources=[shade1, shade2, shade3, shade4, allShades, 
                                                   shadesDown, shadesUpAprSep, shadesUpMayAug, shadesUpJunJul, 
                                                   deckTemp, barometer, humidity, dewpoint])
    restServer = RestServer(resources, event=stateChangeEvent, label="Shades")

    # Start interfaces
    gpioInterface.start()
    shadeInterface.start()
    barometerCache.start()
    humidityCache.start()
    schedule.start()
    restServer.start()

