windSpeedAddr = 22
windDirAddr = 23
rainGaugeAddr = 4
wunderground = True
initialMinTemp = 999
initialMaxTemp = 0

defaultConfig = {
    "rainSamples": [],
    "minTemp": initialMinTemp,
    "maxTemp": initialMaxTemp,
}

from ha import *
from ha.interfaces.gpioInterface import *
from ha.interfaces.i2cInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.bme680Interface import *
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
    stateInterface = FileInterface("fileInterface", fileName=stateDir+"weather.state", event=stateChangeEvent, initialState=defaultConfig)
    weatherInterface = BME680Interface("weatherInterface")
    # weatherCache = TempInterface("weatherCache", weatherInterface, sample=10)

    # Sensors
    deckTemp = Sensor("deckTemp", weatherInterface, "temp", group=["Temperature", "Weather"], label="Deck temp", type="tempF")
    barometer = Sensor("barometer", weatherInterface, "barometer", group="Weather", label="Barometer", type="barometer")
    humidity = Sensor("humidity", weatherInterface, "humidity", group="Weather", label="Humidity", type="humidity")
    dewpoint = Sensor("dewpoint", weatherInterface, "dewpoint", group="Weather", label="Dewpoint", type="tempF")
    # voc = Sensor("voc", weatherInterface, "voc", group="Weather", label="VOC")

    minTemp = MinSensor("minTemp", stateInterface, "minTemp", deckTemp, group=["Weather", "Sprinklers"], type="tempF", label="Min temp")
    maxTemp = MaxSensor("maxTemp", stateInterface, "maxTemp", deckTemp, group=["Weather", "Sprinklers"], type="tempF", label="Max temp")

    anemometer = Sensor("anemometer", gpio1, addr=windSpeedAddr)
    windVane = Sensor("windVane", gpio1, addr=windDirAddr)
    windInterface = WindInterface("windInterface", None, anemometer=anemometer, windVane=windVane) #, event=stateChangeEvent)
    windSpeed = Sensor("windSpeed", windInterface, addr="speed", type="MPH", group="Weather", label="Wind speed")
    windDir = Sensor("windDir", windInterface, addr="dir", type="Deg", group="Weather", label="Wind direction")

    rainGauge = Sensor("rainGauge", gpio1, addr=rainGaugeAddr)
    rainInterface = RainInterface("rainInterface", stateInterface, rainGauge=rainGauge, event=stateChangeEvent)
    rainMinute = Sensor("rainMinute", rainInterface, "minute", type="in", group="Weather", label="Rain per minute")
    rainHour = Sensor("rainHour", rainInterface, "hour", type="in", group="Weather", label="Rain last hour")
    rainDay = Sensor("rainDay", rainInterface, "today", type="in", group="Weather", label="Rain today")
    rainReset = Control("rainReset ", rainInterface, "reset")

    # Tasks
    rainResetTask = Task("rainResetTask", SchedTime(hour=0, minute=0), rainReset, 0, enabled=True)
    resetMinTempTask = Task("resetMinTempTask", SchedTime(hour=0, minute=0), minTemp, initialMinTemp, enabled=True, group="Sprinklers")
    resetMaxTempTask = Task("resetMaxTempTask", SchedTime(hour=0, minute=0), maxTemp, initialMaxTemp, enabled=True, group="Sprinklers")

    # Schedule
    schedule = Schedule("schedule", tasks=[rainResetTask, resetMinTempTask, resetMaxTempTask])

    # Resources
    resources = Collection("resources", resources=[deckTemp, humidity, dewpoint, barometer, # voc,
                                                   windSpeed, windDir, rainMinute, rainHour, rainDay,
                                                   minTemp, maxTemp,
                                                   rainResetTask, resetMinTempTask, resetMaxTempTask,
                                                   ], event=stateChangeEvent)
    restServer = RestServer("weather", resources, label="Weather", event=stateChangeEvent)

    # report to Weather Underground
    if wunderground:
        wunderground(deckTemp, humidity, dewpoint, barometer, windSpeed, windDir, rainHour, rainDay)

    # Start interfaces
    gpio1.start()
    stateInterface.start()
    # weatherSensor.start()
    rainInterface.start()
    schedule.start()
    restServer.start()
