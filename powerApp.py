from ha import *
from ha.interfaces.fileInterface import *
from ha.interfaces.loadInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.bmp085Interface import *
from ha.interfaces.hih6130Interface import *
from ha.interfaces.tempInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    fileInterface = FileInterface("fileInterface", fileName=loadFileName, readOnly=True, event=stateChangeEvent)
    loadInterface = LoadInterface("loadInterface", fileInterface)
    i2c1 = I2CInterface("i2c1", bus=1, event=stateChangeEvent)
    barometerSensor = BMP085Interface("bmp085Interface", i2c1)
    humiditySensor = HIH6130Interface("hih6130Interface", i2c1)
    barometerCache = TempInterface("barometerCache", barometerSensor, sample=10)
    humidityCache = TempInterface("humidityCache", humiditySensor, sample=10)

    # Loads
    lightsLoad = Sensor("lightsLoad", loadInterface, "Lights", group=["Power", "Loads"], label="Lights", type="KVA")
    plugsLoad = Sensor("plugsLoad", loadInterface, "Plugs", group=["Power", "Loads"], label="Plugs", type="KVA")
    appl1Load = Sensor("appl1Load", loadInterface, "Appl1", group=["Power", "Loads"], label="Appliances 1", type="KVA")
    appl2Load = Sensor("appl2Load", loadInterface, "Appl2", group=["Power", "Loads"], label="Appliances 2", type="KVA")
    cookingLoad = Sensor("cookingLoad", loadInterface, "Cooking", group=["Power", "Loads"], label="Stove & oven", type="KVA")
    acLoad = Sensor("acLoad", loadInterface, "Ac", group=["Power", "Loads"], label="Air conditioners", type="KVA")
    poolLoad = Sensor("poolLoad", loadInterface, "Pool", group=["Power", "Loads"], label="Pool equipment", type="KVA")
    backLoad = Sensor("backLoad", loadInterface, "Back", group=["Power", "Loads"], label="Back house", type="KVA")
#    currentLoad = CalcSensor("currentLoad", [lightsLoad, plugsLoad, appl1Load, appl2Load, cookingLoad, acLoad, poolLoad, backLoad], "sum", group=["Power", "Loads"], label="Current load", type="KVA")
    currentLoad = Sensor("currentLoad", loadInterface, "CurrentLoad", group=["Power", "Loads"], label="Current load", type="KVA")
    dailyLoad = Sensor("dailyLoad", loadInterface, "DailyLoad", group=["Power", "Loads"], label="Daily load", type="KVAh")

    # Sensors
    deckTemp = Sensor("deckTemp", barometerCache, "temp", group=["Temperature", "Weather"], label="Deck temp", type="tempF")
    barometer = Sensor("barometer", barometerCache, "barometer", group="Weather", label="Barometer", type="barometer")
    deckTemp2 = Sensor("deckTemp2", humidityCache, "temp", group=["Temperature", "Weather"], label="Deck temp 2", type="tempF")
    humidity = Sensor("humidity", humidityCache, "humidity", group="Weather", label="Humidity", type="humidity")
    dewpoint = Sensor("dewpoint", humidityCache, "dewpoint", group="Weather", label="Dewpoint", type="tempF")

    # Resources
    resources = Collection("resources", resources=[lightsLoad, plugsLoad, appl1Load, appl2Load, cookingLoad, acLoad, poolLoad, backLoad, currentLoad, dailyLoad, 
                                                   deckTemp, barometer, deckTemp2, humidity, dewpoint])
    restServer = RestServer("power", resources=resources, event=stateChangeEvent, label="Loads")

    # Start interfaces
    fileInterface.start()
    loadInterface.start()
    barometerCache.start()
    humidityCache.start()
    restServer.start()
    
