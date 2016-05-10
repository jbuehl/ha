import threading
import time

from ha.HAClasses import *
from ha.fileInterface import *
from ha.timeInterface import *
from ha.I2CInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.imuInterface import *
from ha.restServer import *
from haWeb import *
from adafruit.Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

gpsFileName = "/root/data/gps.json"
diagFileName = "/root/data/diags.json"
imuFileName = "/root/data/9dof.json"

def lcdInit(resources):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    def lcdDisplay():
        lcd = Adafruit_CharLCDPlate(busnum = 1, addr=0x24)
        lcd.backlight(lcd.TEAL)
        while True:
            altitude = resources.getRes("altitude").getState()
            heading = resources.getRes("heading").getState()
            direction = dirs[int((heading+11.25)%360/22.5)]
            outsideTemp = resources.getRes("outsideTemp").getState()
            coolantTemp = resources.getRes("coolantTemp").getState()*9/5+32
            battery = resources.getRes("battery").getState()
            message = "%5d' %03s %03d\n%3dF %3dF %4.1fV" % (altitude, direction, heading, outsideTemp, coolantTemp, battery)
            lcd.clear()
            lcd.message(message)
            time.sleep(10)
    lcdThread = threading.Thread(target=lcdDisplay)
    lcdThread.start()

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    resourceLock = threading.Lock()

    # Interfaces
    stateChangeEvent = threading.Event()
    timeInterface = TimeInterface("Time", tzOffset=-7)
    gpsInterface = FileInterface("GPS", fileName=gpsFileName, readOnly=True, event=stateChangeEvent)
    diagInterface = FileInterface("Diag", fileName=diagFileName, readOnly=True, event=stateChangeEvent)
    ndofInterface = FileInterface("9dof", fileName=imuFileName, readOnly=True, event=stateChangeEvent)
    imuInterface = ImuInterface("IMU", ndofInterface)
    i2cInterface = I2CInterface("I2C", bus=1, event=stateChangeEvent)
    tc74Interface = TC74Interface("TC74", i2cInterface)
    tempInterface = TempInterface("Temp", tc74Interface, sample=1)

    # Sensors
    resources.addRes(HASensor("tacomaDate", timeInterface, "%B %d %Y", group="Tacoma", label="Date", type="date"))
    resources.addRes(HASensor("tacomaTimeAmPm", timeInterface, "%I:%M %p", group="Tacoma", label="Time", type="time"))
#    resources.addRes(HASensor("gpsTime", gpsInterface, "Time", group="Tacoma", label="GPS time"))
    resources.addRes(HASensor("position", gpsInterface, "Pos", group="Tacoma", label="Position"))
    resources.addRes(HASensor("altitude", gpsInterface, "Alt", group="Tacoma", label="Elevation", type="Ft"))
    resources.addRes(HASensor("heading", gpsInterface, "Hdg", group="Tacoma", label="Heading", type="Deg"))
    resources.addRes(HASensor("gpsSpeed", gpsInterface, "Speed", group="Tacoma", label="GPS speed", type="MPH"))
    resources.addRes(HASensor("speed", diagInterface, "Speed", group="Tacoma", label="Speed", type="MPH"))
    resources.addRes(HASensor("rpm", diagInterface, "Rpm", group="Tacoma", label="RPM", type="RPM"))
    resources.addRes(HASensor("battery", diagInterface, "Battery", group="Tacoma", label="Battery", type="V"))
    resources.addRes(HASensor("intakeTemp", diagInterface, "IntakeTemp", group="Tacoma", label="Intake air temp", type="tempC"))
    resources.addRes(HASensor("coolantTemp", diagInterface, "WaterTemp", group="Tacoma", label="Water temp", type="tempC"))
    resources.addRes(HASensor("airPressure", diagInterface, "Barometer", group="Tacoma", label="Barometer", type="barometer"))
    resources.addRes(HASensor("outsideTemp", tempInterface, 0x4e, group="Tacoma", label="Outside temp", type="tempF"))

    # Start interfaces
    gpsInterface.start()
    diagInterface.start()
    ndofInterface.start()
    tempInterface.start()

    # set up the LCD
    lcdInit(resources)
    
    # set up the web server
    webInit(resources, None, stateChangeEvent, resourceLock)

    # start the REST server for this service
    restServer = RestServer(resources, event=stateChangeEvent, label="Tacoma")
    restServer.start()
    
