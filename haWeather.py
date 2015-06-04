import threading

from ha.HAClasses import *
from ha.I2CInterface import *
from ha.BMP085Interface import *
from ha.HIH6130Interface import *
from ha.tempInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    i2c1 = I2CInterface("I2C1", bus=1, event=stateChangeEvent)
    barometer = BMP085Interface("BMP085", i2c1)
    humidity = HIH6130Interface("HIH6130", i2c1)
    barometerCache = TempInterface("barometerCache", barometer, sample=10)
    humidityCache = TempInterface("humidityCache", humidity, sample=10)
    
    # Temperature
    resources.addRes(HASensor("deckTemp", barometerCache, "temp", group="Temperature", label="Deck temp", type="tempF"))
    resources.addRes(HASensor("barometer", barometerCache, "barometer", group="Temperature", label="Barometer", type="barometer"))
    resources.addRes(HASensor("humidity", humidityCache, "humidity", group="Temperature", label="Humidity", type="humidity"))
    
    # Start interfaces
    barometerCache.start()
    humidityCache.start()
    restServer = RestServer(resources, port=7379, event=stateChangeEvent, label="Weather")
    restServer.start()

