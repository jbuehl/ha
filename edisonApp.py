
tempType = "tc74"
tempAddr = 0x4b
tempSample = 10

import sys
from ha import *
from ha.interfaces.i2cCmdInterface import *
from ha.interfaces.tc74Interface import *
from ha.interfaces.mcp9803Interface import *
#from ha.interfaces.bmp085Interface import *
#from ha.interfaces.hih6130Interface import *
from ha.interfaces.tempInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    # Interfaces
    stateChangeEvent = threading.Event()
    i2cInterface = I2CCmdInterface("i2cInterface", bus=1, event=stateChangeEvent)
    tc74Interface = TC74Interface("TC74Interface", i2cInterface)
    mcp9803Interface = MCP9803Interface("MCP9803Interface", i2cInterface)
    if tempType.upper() == "TC74":
        tempInterface = TempInterface("tempInterface", tc74Interface, sample=tempSample)
    elif tempType.upper() == "MCP9803":
        tempInterface = TempInterface("tempInterface", mcp9803Interface, sample=tempSample)
    else:
        log("error", "unknown tempType", tempType)
        sys.exit(1)
#    barometer = BMP085Interface("bmp085Interface", i2cInterface)
#    humidity = HIH6130Interface("hih6130Interface", i2cInterface)
#    barometerCache = TempInterface("barometerCache", barometer, sample=10)
#    humidityCache = TempInterface("humidityCache", humidity, sample=10)
    
    # Temperature
    edisonTemp = Sensor("edisonTemp", tempInterface, tempAddr, group=["Temperature", "Weather"], label="Edison temp", type="tempF")
#    deckTemp = Sensor("deckTemp", barometerCache, "temp", group=["Temperature", "Weather"], label="Deck temp", type="tempF")
#    barometer = Sensor("barometer", barometerCache, "barometer", group="Weather", label="Barometer", type="barometer")
#    deckTemp2 = Sensor("deckTemp2", humidityCache, "temp", group=["Temperature", "Weather"], label="Deck temp 2", type="tempF")
#    humidity = Sensor("humidity", humidityCache, "humidity", group="Weather", label="Humidity", type="humidity")
#    dewpoint = Sensor("dewpoint", humidityCache, "dewpoint", group="Weather", label="Dewpoint", type="tempF")
    
    # Resources
    resources = Collection("resources",resources=[edisonTemp, 
#                                                 deckTemp, barometer, deckTemp2, humidity, dewpoint
                                                 ])
    restServer = RestServer("edison", resources, event=stateChangeEvent, label="Edison")

    # Start interfaces
    tempInterface.start()
#    barometerCache.start()
#    humidityCache.start()
    restServer.start()

