webPort = 80
webSSLPort = 7380
webSSLDomain = "cloud.buehltech.com"
webUpdateInterval = 1
webPageTitle = "Home Automation"
runRestServer = True
runCameras = True
runMetrics = True
runEvents = True
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
from ha.interfaces.timeInterface import *
from ha.interfaces.fileInterface import *
from ha.interfaces.osInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *
from ha.rest.restProxy1 import *
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
    ts = time.time()
    debug('debugWeb', "/", "start", ts)
    result = dashboardUI(resources, templates, views)
    debug('debugWeb', "/", "end", ts)
    return result

# show all resource details or specified group
def details(group=None):
    debug('debugWeb', "/details", group)
    try:
        groups = [[group.capitalize(), resources.getGroup(group)]]
        details = True
    except:
        groups = [[group, resources.getGroup(group)] for group in ["Alerts", "Services", "System",
                                                                    "Time", "Weather", "Temperature",
                                                                    "Hvac", "Pool", "Lights", "Shades", "Doors", "Car",
                                                                    "Sprinklers", "Water", "Loads", "Solar",
                                                                    "Tasks"]]
        details = True
    with resources.lock:
        screenWidth = 1280
        labelWidth = 220
        widths = [screenWidth, [labelWidth, 160, 260, 120, 100, 120, 240, 60]]
        result = templates.get_template("details.html").render(title=webPageTitle, script="",
                            templates=templates,
                            widths=widths,
                            groups=groups,
                            views=views,
                            details=details,
                            link=False)
        # print("detail", len(result))
        return result

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
    resources = Collection("resources", aliases=aliases, event=stateChangeEvent)

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
    resources.addRes(Sensor("system."+hostname+".cpuLoad", osInterface, "cpuLoad", type="pct", group="System", label=hostname+" CPU load"))
    resources.addRes(Sensor("system."+hostname+".uptime", osInterface, "uptime", group="System", label=hostname+" Uptime"))
    resources.addRes(Sensor("system."+hostname+".ipAddr", osInterface, "ipAddr eth0", group="System", label=hostname+" IP address"))
    resources.addRes(Sensor("system.cameras.usage", osInterface, "diskUse /mnt/disk1", type="pct", group="System", label="Camera disk usage"))
    resources.addRes(Sensor("system.backups.usage", osInterface, "diskUse /mnt/disk2", type="pct", group="System", label="Backup disk usage"))

    stateInterface = FileInterface("stateInterface", fileName=stateDir+"ha.state", event=stateChangeEvent, initialState=defaultConfig)
    stateInterface.start()
    smsAlerts = Control("smsAlerts", stateInterface, "smsAlerts", group="Alerts", label="SMS alerts")
    appAlerts = Control("appAlerts", stateInterface, "appAlerts", group="Alerts", label="App alerts")
    iftttAlerts = Control("iftttAlerts", stateInterface, "iftttAlerts", group="Alerts", label="IFTTT alerts")
    alertServices = Control("alertServices", stateInterface, "alertServices", group="Alerts", label="Service down")
    alertSpa = Control("alertSpa", stateInterface, "alertSpa", group="Alerts", label="Spa is ready")
    alertDoorbell = Control("alertDoorbell", stateInterface, "alertDoorbell", group="Alerts", label="Doorbell")
    alertDoors = Control("alertDoors", stateInterface, "alertDoors", group="Alerts", label="Door opened")
    alertMotion = Control("alertMotion", stateInterface, "alertMotion", group="Alerts", label="Motion")
    resources.addRes(smsAlerts)
    resources.addRes(appAlerts)
    resources.addRes(iftttAlerts)
    resources.addRes(alertServices)
    resources.addRes(alertSpa)
    resources.addRes(alertDoorbell)
    resources.addRes(alertDoors)
    resources.addRes(alertMotion)

    # start the task to transmit resource metrics
    if runMetrics:
        startMetrics(resources, sendMetrics, logMetrics, backupMetrics)

    # start the cache to listen for services on other servers
    restCache = RestProxy("restCache", resources, watch=restWatch, ignore=restIgnore+["house"], event=stateChangeEvent)
    restCache.start()

    # start the cache to listen for legacy services on ESP devices
    espRestCache = RestProxy1("espRestCache", resources, event=stateChangeEvent)
    espRestCache.start()

    # monitor service states
    if runEvents:
        watchEvents(resources)

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
        restServer = RestServer("house", resources, port=restServicePort, notify=False, event=stateChangeEvent, label="House")
        restServer.start()
