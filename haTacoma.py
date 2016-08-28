rootDir = "/root/"
dataDir = rootDir+"data/"
audioDir = "audio/"
gpsFileName = dataDir+"gps.json"
diagFileName = dataDir+"diags.json"
imuFileName = dataDir+"9dof.json"
audioFileName = audioDir+"audio.json"
httpPort = 8080

import threading
import time
import cherrypy
from jinja2 import Environment, FileSystemLoader

from ha.HAClasses import *
from ha.fileInterface import *
from ha.timeInterface import *
from ha.I2CInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.imuInterface import *
from ha.audioInterface import *
from ha.restServer import *
from ha.haWeb import *

# global variables
templates = None
resources = None
stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

# Tacoma - 800x480
def tacoma():
    debug('debugWeb', "/tacoma", cherrypy.request.method)
    with resourceLock:
        reply = templates.get_template("tacoma.html").render(title=webPageTitle, script="", 
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            temp=resources.getRes("outsideTemp"),
                            controls=[resources.getRes("volume"),
                                      resources.getRes("mute"),
                                      resources.getRes("wifi"),
                                     ],
                            group=resources.getGroup("Tacoma"),
                            views=views)
    return reply

# dispatch table
pathDict = {"": tacoma,
            "tacoma": tacoma,
            }
            
if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    timeInterface = TimeInterface("Time")
    gpsInterface = FileInterface("GPS", fileName=gpsFileName, readOnly=True, event=stateChangeEvent)
    diagInterface = FileInterface("Diag", fileName=diagFileName, readOnly=True, event=stateChangeEvent)
    ndofInterface = FileInterface("9dof", fileName=imuFileName, readOnly=True, event=stateChangeEvent)
    imuInterface = ImuInterface("IMU", ndofInterface)
    i2cInterface = I2CInterface("I2C", bus=1, event=stateChangeEvent)
    tc74Interface = TC74Interface("TC74", i2cInterface)
    tempInterface = TempInterface("Temp", tc74Interface, sample=1)
    audioInterface = AudioInterface("Audio", event=stateChangeEvent)

    # time sensors
    resources.addRes(HASensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(HASensor("theDate", timeInterface, "%B %d %Y", type="date", group="Time", label="Date"))
    resources.addRes(HASensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(HASensor("sunrise", timeInterface, "sunrise", type="time", group="Time", label="Sunrise"))
    resources.addRes(HASensor("sunset", timeInterface, "sunset", type="time", group="Time", label="Sunset"))
    resources.addRes(HASensor("theDay", timeInterface, "%a %b %d %Y", type="date", label="Day"))
    resources.addRes(HASensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(HASensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    # GPS sensors
#    resources.addRes(HASensor("gpsTime", gpsInterface, "Time", group="Tacoma", label="GPS time"))
    resources.addRes(HASensor("position", gpsInterface, "Pos", group="Tacoma", label="Position"))
    resources.addRes(HASensor("altitude", gpsInterface, "Alt", group="Tacoma", label="Elevation", type="Ft"))
    resources.addRes(HASensor("heading", gpsInterface, "Hdg", group="Tacoma", label="Heading", type="Deg"))
#    resources.addRes(HASensor("gpsSpeed", gpsInterface, "Speed", group="Tacoma", label="GPS speed", type="MPH"))

    # diag sensors
#    resources.addRes(HASensor("speed", diagInterface, "Speed", group="Tacoma", label="Speed", type="MPH"))
    resources.addRes(HASensor("rpm", diagInterface, "Rpm", group="Tacoma", label="RPM", type="RPM"))
    resources.addRes(HASensor("battery", diagInterface, "Battery", group="Tacoma", label="Battery", type="V"))
#    resources.addRes(HASensor("intakeTemp", diagInterface, "IntakeTemp", group="Tacoma", label="Intake air temp", type="tempC"))
    resources.addRes(HASensor("coolantTemp", diagInterface, "WaterTemp", group="Tacoma", label="Water temp", type="tempC"))
    resources.addRes(HASensor("airPressure", diagInterface, "Barometer", group="Tacoma", label="Barometer", type="barometer"))
    resources.addRes(HASensor("outsideTemp", tempInterface, 0x4e, group="Temp", label="Outside temp", type="tempF"))

    # Controls
    resources.addRes(HAControl("volume", audioInterface, "volume", group="Audio", label="Vol", type="audioVolume"))
    resources.addRes(HAControl("mute", audioInterface, "mute", group="Audio", label="Mute", type="audioMute"))
    resources.addRes(HAControl("wifi", audioInterface, "wifi", group="Audio", label="Wifi", type="wifi"))
    
    # Start interfaces
    gpsInterface.start()
    diagInterface.start()
    ndofInterface.start()
    tempInterface.start()

    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    templates = Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates')))
    webInit(resources, None, stateChangeEvent, resourceLock, httpPort=httpPort, pathDict=pathDict, baseDir=baseDir, block=True)

