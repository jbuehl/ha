windSpeedAddr = 22
windDirAddr = 23
rainGaugeAddr = 4
wunderground = True

defaultConfig = {"rainSamples": []}

from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.bmp085Interface import *
from ha.interfaces.hih6130Interface import *
from ha.interfaces.tempInterface import *
from ha.interfaces.windInterface import *
from ha.interfaces.rainInterface import *
from ha.rest.restServer import *
from ha.notification.notificationClient import *
from ha.wunderground import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    i2c1 = I2CInterface("i2c1", bus=1)
    gpio1 = GPIOInterface("gpio1", input=[windSpeedAddr, windDirAddr, rainGaugeAddr])
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"weather.state", event=stateChangeEvent, initialState=defaultConfig)
    barometerSensor = BMP085Interface("bmp085Interface", i2c1)
    humiditySensor = HIH6130Interface("hih6130Interface", i2c1)
    barometerCache = TempInterface("barometerCache", barometerSensor, sample=10)
    humidityCache = TempInterface("humidityCache", humiditySensor, sample=10)

    # Sensors
    deckTemp2 = Sensor("deckTemp2", barometerCache, "temp", group=["Temperature", "Weather"], label="Deck temp 2", type="tempF")
    barometer = Sensor("barometer", barometerCache, "barometer", group="Weather", label="Barometer", type="barometer")
    deckTemp = Sensor("deckTemp", humidityCache, "temp", group=["Temperature", "Weather"], label="Deck temp", type="tempF")
    humidity = Sensor("humidity", humidityCache, "humidity", group="Weather", label="Humidity", type="humidity")
    dewpoint = Sensor("dewpoint", humidityCache, "dewpoint", group="Weather", label="Dewpoint", type="tempF")

    anemometer = Sensor("anemometer", gpio1, addr=windSpeedAddr)
    windVane = Sensor("windVane", gpio1, addr=windDirAddr)
    windInterface = WindInterface("windInterface", None, anemometer=anemometer, windVane=windVane)
    windSpeed = Sensor("windSpeed", windInterface, addr="speed", type="MPH", group="Weather", label="Wind speed")
    windDir = Sensor("windDir", windInterface, addr="dir", type="Deg", group="Weather", label="Wind direction")

    rainGauge = Sensor("rainGauge", gpio1, addr=rainGaugeAddr)
    rainInterface = RainInterface("rainInterface", fileInterface, rainGauge=rainGauge)
    rainMinute = Sensor("rainMinute", rainInterface, "minute", type="in", group="Weather", label="Rain per minute")
    rainHour = Sensor("rainHour", rainInterface, "hour", type="in", group="Weather", label="Rain last hour")
    rainDay = Sensor("rainDay", rainInterface, "today", type="in", group="Weather", label="Rain today")
    rainReset = Control("rainReset ", rainInterface, "reset")

    # Tasks
    rainResetTask = Task("rainResetTask", SchedTime(hour=0, minute=0), rainReset, 0, enabled=True)

    # Schedule
    schedule = Schedule("schedule", tasks=[rainResetTask])

    # Resources
    resources = Collection("resources", resources=[deckTemp, deckTemp2, humidity, dewpoint, barometer,
                                                   windSpeed, windDir, rainMinute, rainHour, rainDay,
                                                   ])
    restServer = RestServer("weather", resources, event=stateChangeEvent, label="Weather")

    # report to Weather Underground
    if wunderground:
        wunderground(deckTemp, humidity, dewpoint, barometer, windSpeed, windDir, rainHour, rainDay)

    # Start interfaces
    gpio1.start()
    fileInterface.start()
    barometerCache.start()
    humidityCache.start()
    rainInterface.start()
    schedule.start()
    restServer.start()
