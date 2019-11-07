webPort = 80
webSSLPort = 7380
webSSLDomain = "cloud.buehltech.com"
webUpdateInterval = 1
webPageTitle = "Home Automation"
runRestServer = True
runCameras = True
restWatch = []
restIgnore = []
serviceMonitorNotifyNumbers = []
sendMetrics = True
logMetrics = True
backupMetrics = False
logDir = "/data/ha/"

defaultConfig = {
    "smsAlerts": True,
    "appAlerts": False,
    "iftttAlerts": True,
    "alertServices": True,
    "alertSpa": True,
    "alertDoorbell": True,
    "alertDoors": False,
}

import time
import socket
from jinja2 import Environment, FileSystemLoader
from ha import *
from ha.metrics import *
from ha.eventMonitor import *
from ha.interfaces.restInterface import *
from ha.interfaces.timeInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.osInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *
from ha.ui.webUI import *
from ha.ui.dashboardUI import *
from ha.ui.ipadUI import *
from ha.ui.iphoneUI import *
from ha.ui.bedroomUI import *
from ha.ui.solarUI import *
from ha.ui.networkUI import *
from ha.ui.cameraUI import *
from ha.camera.classes import *

# global variables
templates = None
resources = None
cameras = None
stateChangeEvent = threading.Event()

# default - dashboard
def index():
    debug('debugWeb', "/")
    return dashboardUI(resources, templates, views)

# show all resource details or specified group
def details(group=None):
    debug('debugWeb', "/detail", group)
    try:
        groups = [[group.capitalize(), resources.getGroup(group)]]
        details = True
    except:
        groups = [[group, resources.getGroup(group)] for group in ["Alerts", "Services", "Time", "Weather", "Temperature",
                    "Hvac", "Pool", "Lights", "Shades", "Doors", "Car",
                    "Sprinklers", "Water", "Loads", "Solar",
                    "Tasks"]]
        details = True
    with resources.lock:
        screenWidth = 1280
        labelWidth = 220
        widths = [screenWidth, [labelWidth, 160, 260, 120, 100, 120, 240, 60]]
        return templates.get_template("details.html").render(title=webPageTitle, script="",
                            templates=templates,
                            widths=widths,
                            groups=groups,
                            views=views,
                            details=details,
                            link=False)

# iPad - 1024x768
def ipad(location=""):
    debug('debugWeb', "/ipad", cherrypy.request.method)
    return ipadUI(location, resources, templates, views)

# generic iPhone
def iphone():
    debug('debugWeb', "/iphone", cherrypy.request.method)
    return iphoneUI(resources, templates, views)

# iPhone 3 - 320x480
def bedroom():
    debug('debugWeb', "/bedroom", cherrypy.request.method)
    return bedroomUI(resources, templates, views)

# Solar
def solar():
    debug('debugWeb', "/solar", cherrypy.request.method)
    return solarUI(resources, templates, views)

# Cameras
def cameras(function=None, camera=None, date=None, resource=None):
    debug('debugWeb', "/cameras", cherrypy.request.method)
    return cameraUI(function, camera, date, resource, cameras, resources, templates, views)

# Network statistics
def network(order=None):
    debug('debugWeb', "/network", cherrypy.request.method)
    return networkUI(order, templates, views)

# dispatch table
pathDict = {"": index,
            "details": details,
            "solar": solar,
            "cameras": cameras,
            "network": network,
            "ipad": ipad,
            "iphone": iphone,
            "bedroom": bedroom,
            }

if __name__ == "__main__":
    waitForDns()
    # initialize resources
    try:
        with open(rootDir+"aliases") as aliasFile:
            aliases = json.load(aliasFile)
    except:
        aliases = {}
    resources = Collection("resources", aliases=aliases)

    # add local resources
    timeInterface = TimeInterface("timeInterface", None, latLong=latLong)
    resources.addRes(Sensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(Sensor("theDateDayOfWeek", timeInterface, "%a %B %-d %Y", type="date", label="Date"))
    resources.addRes(Sensor("theDate", timeInterface, "%B %-d %Y", type="date", group="Time", label="Date"))
    resources.addRes(Sensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(Sensor("theTimeZone", timeInterface, "timeZone", type="time", group="Time", label="Time zone"))
    resources.addRes(Sensor("theTimeZoneName", timeInterface, "timeZoneName", type="time", group="Time", label="Time zone name"))
    resources.addRes(Sensor("sunrise", timeInterface, "sunrise", type="time", group="Time", label="Sunrise"))
    resources.addRes(Sensor("sunset", timeInterface, "sunset", type="time", group="Time", label="Sunset"))
    resources.addRes(Sensor("theDay", timeInterface, "%a %b %-d %Y", type="date", label="Day"))
    resources.addRes(Sensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(Sensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    osInterface = OSInterface("osInterface")
    resources.addRes(Sensor("system."+hostname+".cpuTemp", osInterface, "cpuTemp", type="tempC", group="System", label=hostname+" CPU temp"))
    resources.addRes(Sensor("system."+hostname+".uptime", osInterface, "uptime", group="System", label=hostname+" Uptime"))
    resources.addRes(Sensor("system."+hostname+".ipAddr", osInterface, "ipAddr eth0", group="System", label=hostname+" IP address"))
    resources.addRes(Sensor("system.disk1.usage", osInterface, "diskUse /mnt/disk1", type="pct", group="System", label="Disk1 usage"))
    resources.addRes(Sensor("system.disk2.usage", osInterface, "diskUse /mnt/disk2", type="pct", group="System", label="Disk2 usage"))

    stateInterface = FileInterface("stateInterface", fileName=stateDir+"ha.state", event=stateChangeEvent, initialState=defaultConfig)
    stateInterface.start()
    smsAlerts = Control("smsAlerts", stateInterface, "smsAlerts", group="Alerts", label="Send SMS alerts")
    appAlerts = Control("appAlerts", stateInterface, "appAlerts", group="Alerts", label="Send app alerts")
    iftttAlerts = Control("iftttAlerts", stateInterface, "iftttAlerts", group="Alerts", label="Send IFTTT alerts")
    alertServices = Control("alertServices", stateInterface, "alertServices", group="Alerts", label="Service down")
    alertSpa = Control("alertSpa", stateInterface, "alertSpa", group="Alerts", label="Spa is ready")
    alertDoorbell = Control("alertDoorbell", stateInterface, "alertDoorbell", group="Alerts", label="Doorbell")
    alertDoors = Control("alertDoors", stateInterface, "alertDoors", group="Alerts", label="Door opened")
    resources.addRes(smsAlerts)
    resources.addRes(appAlerts)
    resources.addRes(iftttAlerts)
    resources.addRes(alertServices)
    resources.addRes(alertSpa)
    resources.addRes(alertDoorbell)
    resources.addRes(alertDoors)

    # start the task to transmit resource metrics
    resourceStates = ResourceStateSensor("states", None, resources=resources, event=stateChangeEvent)
    startMetrics(resourceStates, sendMetrics, logMetrics, backupMetrics)

    # start the cache to listen for services on other servers
    restCache = RestProxy("restProxy", resources, watch=restWatch, ignore=restIgnore, event=stateChangeEvent)
    restCache.start()

    # monitor service states
    watchEvents(resources, serviceMonitorNotifyNumbers)

    # get the camera attributes
    if runCameras:
        cameras = getCameras()

    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    templates = Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates')))
    webInit(resources, restCache, stateChangeEvent, httpPort=webPort,
#            ssl=True, httpsPort=webSSLPort, domain=webSSLDomain,
            pathDict=pathDict, baseDir=baseDir, block=not runRestServer)

    # start the REST server
    if runRestServer:
        restServer = RestServer("house", resources, port=restServicePort, beacon=False, heartbeat=False, event=stateChangeEvent, label="House")
        restServer.start()
