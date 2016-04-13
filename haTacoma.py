import threading

from ha.HAClasses import *
from ha.fileInterface import *
from ha.timeInterface import *
from ha.I2CCmdInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.restServer import *
from haWeb import *

gpsFileName = "/root/data/gps.json"
diagFileName = "/root/data/diags.json"

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    resourceLock = threading.Lock()

    # Interfaces
    stateChangeEvent = threading.Event()
    timeInterface = TimeInterface("Time", tzOffset=-7)
    gpsInterface = FileInterface("GPS", fileName=gpsFileName, readOnly=True, event=stateChangeEvent)
    diagInterface = FileInterface("Diag", fileName=diagFileName, readOnly=True, event=stateChangeEvent)
    i2cInterface = I2CCmdInterface("I2C", bus=1, event=stateChangeEvent)
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
    resources.addRes(HASensor("barometer", diagInterface, "Barometer", group="Tacoma", label="Barometer", type="barometer"))
    resources.addRes(HASensor("outsideTemp", tempInterface, 0x4f, group="Tacoma", label="Outside temp", type="tempF"))

    # Start interfaces
    gpsInterface.start()
    diagInterface.start()
    tempInterface.start()

    # set up the web server
    webInit(resources, None, stateChangeEvent, resourceLock)

    # start the REST server for this service
    restServer = RestServer(resources, event=stateChangeEvent, label="Tacoma")
    restServer.start()
    
