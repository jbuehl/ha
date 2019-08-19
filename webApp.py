webPort = 80
webSSLPort = 7380
webSSLDomain = "cloud.buehltech.com"
webUpdateInterval = 1
webPageTitle = "Home Automation"
runRestServer = True
restWatch = []
restIgnore = []
insideTemp = "diningRoomTemp"
outsideTemp = "edisonTemp"
poolTemp = "poolTemp"
serviceMonitorNotifyNumbers = []

defaultConfig = {
    "alertServices": True,
    "alertDoorbell": True,
    "alertDoors": False,
}

import time
from jinja2 import Environment, FileSystemLoader
from ha import *
from ha.metrics import *
from ha.serviceMonitor import *
from ha.interfaces.restInterface import *
from ha.interfaces.timeInterface import *
from ha.interfaces.fileInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *
from ha.ui.webUI import *
from ha.ui.dashboardUI import *

# global variables
templates = None
resources = None
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
    with resources.lock:
        screenWidth = 1024
        labelWidth = 194
        columnWidth = screenWidth/2
        columnWidths = [columnWidth, [labelWidth, 120, 190]]
        headerWidths = [screenWidth, [432, 180, 180, 180]]
        widths = [screenWidth, [columnWidths, columnWidths]]
        widths = [headerWidths, [screenWidth, [columnWidths, columnWidths]]]
        if location == "backhouse":
            location = "Back house"
            lightsGroup=["Lights", resources.getResList(["backLights", "poolLight", "spaLight"])]
            hvac = templates.get_template("hvacWidget.html").render(label="Inside temp",
                    widths=columnWidths,
                    templates=templates,
                    tempSensor=resources.getRes("backHouseTemp"),
                    heatTargetControl=resources.getRes("backHeatTempTarget"),
                    coolTargetControl=resources.getRes("backCoolTempTarget"),
                    fanControl=resources.getRes("backFan"),
                    thermostatUnitSensor=resources.getRes("backThermostatUnitSensor"),
                    views=views)
            shadesGroup = []
        else:
            location = "Kitchen"
            lightsGroup=["Lights", resources.getResList(["porchLights", "poolLight", "spaLight"])]
            hvac = templates.get_template("hvacWidget.html").render(label="Inside temp",
                    widths=columnWidths,
                    templates=templates,
                    tempSensor=resources.getRes("diningRoomTemp"),
                    heatTargetControl=resources.getRes("southHeatTempTarget"),
                    coolTargetControl=resources.getRes("southCoolTempTarget"),
                    thermostatUnitSensor=resources.getRes("southThermostatUnitSensor"),
                    views=views)
            shadesGroup=["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])]
        reply = templates.get_template("ipad.html").render(script="",
                            templates=templates,
                            widths=widths,
                            location=location,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            pooltemp=resources.getRes("poolTemp"),
                            outtemp=resources.getRes(outsideTemp),
                            humidity=resources.getRes("humidity"),
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            poolPumpControl=resources.getRes("poolPump"),
                            poolPumpFlowSensor=resources.getRes("poolPumpFlow"),
                            lightsGroup=lightsGroup,
#                           xmasGroup=["Lights", resources.getResList(["porchLights", "xmasLights", "xmasTree"])],
#                                      ["Lights", resources.getResList(["bbqLights", "backYardLights"])],
#                                      ["Lights", resources.getResList(["xmasTree", "xmasCowTree", "xmasLights"])],
                            shadesGroup=shadesGroup,
                            hvac=hvac,
                            sprinklersGroup=["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "backBedSequence",
                                                                                 "sideBedSequence", "frontLawnSequence", "frontBedSequence"])],
                            views=views)
    return reply

# iPhone 5 - 320x568
def iphone5():
    debug('debugWeb', "/iphone5", cherrypy.request.method)
    with resources.lock:
        widths = [[320, [60, 100, 60]], [320, [120, 72, 128]]]
        reply = templates.get_template("iphone5.html").render(script="",
                            templates=templates,
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            temp=resources.getRes(outsideTemp),
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            poolPumpControl=resources.getRes("poolPump"),
                            poolPumpFlowSensor=resources.getRes("poolPumpFlow"),
                            resources=resources.getResList(["spaBlower", "porchLights",
#                                                            "xmasLights", "xmasTree",
                                                            "shade1", "shade2", "shade3", "shade4",
                                                            "backLawnSequence", "backBedSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence", "frontBedSequence"
                                                            ]),
                            views=views)
    return reply

# iPhone 3GS - 320x480
def iphone3gs():
    debug('debugWeb', "/iphone3gs", cherrypy.request.method)
    with resources.lock:
        widths = [[320, [296, 24]], [320, [240, 80]], [320, [152, 168]]]
        northHvac = templates.get_template("hvacWidget.html").render(label="Temperature",
                            widths=widths[2],
                            templates=templates,
                            stack=True,
                            resourceTemplate=templates.get_template("resource.html"),
                            tempSensor=resources.getRes("masterBedroomTemp"),
                            heatTargetControl=resources.getRes("northHeatTempTarget"),
                            coolTargetControl=resources.getRes("northCoolTempTarget"),
                            thermostatUnitSensor=resources.getRes("northThermostatUnitSensor"),
                            views=views)
        reply = templates.get_template("iphone3gs.html").render(script="",
                            templates=templates,
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            temp=resources.getRes(outsideTemp),
                            hvac=northHvac,
                            resources=resources.getResList(["porchLights",
#                                                            "xmasLights",
                                                            "bedroomLights", "recircPump", "garageDoors", "houseDoors", "backHouseDoor"]),
                            views=views)
    return reply

# Solar
def solar():
    debug('debugWeb', "/solar", cherrypy.request.method)
    with resources.lock:
        optimizers = []
        opts = resources.getGroup("Optimizers")
        for opt in opts:
            if opt.name[-5:] == "power":
                if opt.name[-14:-6] in ["100F71E5", "100F7255"]:
                    panel = ["ppanel", opt.location[0]+18, opt.location[1]-17]
                else:
                    panel = ["lpanel", opt.location[0]+1, opt.location[1]+1]
                optimizers.append([opt, resources.getRes(opt.name[0:-5]+"temp"), panel])
        return templates.get_template("solar.html").render(script="",
                            dayOfWeek=resources.getRes("theDayOfWeek"),
                            date=resources.getRes("theDate"),
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            sunrise=resources.getRes("sunrise"),
                            sunset=resources.getRes("sunset"),
                            latitude="%7.3f "%(abs(latLong[0])+.0005)+("N" if latLong[0]>0 else "S"),
                            longitude="%7.3f "%(abs(latLong[1])+.0005)+("E" if latLong[1]>0 else "W"),
                            elevation="%d ft"%(elevation),
                            airTemp=resources.getRes(outsideTemp),
                            inverterTemp=resources.getRes("solar.inverters.stats.avgTemp"),
                            roofTemp=resources.getRes("solar.optimizers.stats.avgTemp"),
                            currentVoltage=resources.getRes("solar.inverters.stats.avgVoltage"),
                            currentLoad=resources.getRes("loads.stats.power"),
                            currentPower=resources.getRes("solar.inverters.stats.power"),
                            todaysEnergy=resources.getRes("solar.inverters.stats.dailyEnergy"),
                            lifetimeEnergy=resources.getRes("solar.inverters.stats.lifetimeEnergy"),
                            inverters=resources.getGroup("Inverters"),
                            optimizers=optimizers,
                            views=views)

# Weather
def weather():
    debug('debugWeb', "/weather", cherrypy.request.method)
    with resources.lock:
        return templates.get_template("weather.html").render(script="",
                            )

# dispatch table
pathDict = {"": index,
            "details": details,
            "solar": solar,
            "weather": weather,
            "ipad": ipad,
            "iphone5": iphone5,
            "iphone3gs": iphone3gs,
            }

if __name__ == "__main__":
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

    stateInterface = FileInterface("stateInterface", fileName=stateDir+"ha.state", event=stateChangeEvent, initialState=defaultConfig)
    stateInterface.start()
    alertServices = Control("alertServices", stateInterface, "alertServices", group="Alerts", label="Alert services")
    alertDoorbell = Control("alertDoorbell", stateInterface, "alertDoorbell", group="Alerts", label="Alert doorbell")
    alertDoors = Control("alertDoors", stateInterface, "alertDoors", group="Alerts", label="Alert doors")
    resources.addRes(alertServices)
    resources.addRes(alertDoorbell)
    resources.addRes(alertDoors)


    # light groups
    porchLights = ControlGroup("porchLights", ["frontLights",
                                               "sculptureLights",
                                               "holidayLights",
                                               "backLights",
                                               # "deckLights",
                                               "garageBackDoorLight"],
                                               resources=resources,
                                               type="light", group="Lights", label="Porch lights")
    xmasLights = ControlGroup("xmasLights", ["xmasTree",
                                               "xmasCowTree",
                                               "xmasBackLights"],
                                               resources=resources,
                                               type="light", group=["Lights", "Xmas"], label="Xmas lights")
    bedroomLights = ControlGroup("bedroomLights", ["bedroomLight",
                                               "bathroomLight"],
                                               resources=resources,
                                               stateList=[[0, 100, 0], [0, 100, 10]],
                                               type="nightLight", group="Lights", label="Night lights")
    outsideLights = ControlGroup("outsideLights", ["frontLights",
                                               "sculptureLights",
                                               "backLights",
                                               "garageBackDoorLight",
                                               "bbqLights",
                                               "backYardLights",
                                               "deckLights",
                                               "trashLights",
                                               "poolLights",
                                               "holidayLights",
                                               "xmasTree",
                                               "xmasCowTree",
                                               "xmasBackLights"],
                                               resources=resources,
                                               type="light", group="Lights", label="Outside lights")
    resources.addRes(porchLights)
    resources.addRes(xmasLights)
    resources.addRes(bedroomLights)
    resources.addRes(outsideLights)

    # Light tasks
    resources.addRes(Task("bedroomLightsOnSunset", SchedTime(event="sunset"), "bedroomLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("bedroomLightsOffSunrise", SchedTime(event="sunrise"), "bedroomLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("porchLightsOnSunset", SchedTime(event="sunset"), "porchLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("outsideLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("outsideLightsOffSunrise", SchedTime(event="sunrise"), "outsideLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOnSunset", SchedTime(event="sunset"), "xmasLights", 1, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffMidnight", SchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=resources, group="Lights"))
    resources.addRes(Task("xmasLightsOffSunrise", SchedTime(event="sunrise"), "xmasLights", 0, resources=resources, group="Lights"))
#        resources.addRes(Task("xmasTreeOnXmas", SchedTime(month=[12], day=[25], hour=[7], minute=[00]), "xmasTree", 1, resources=resources))

    # Light schedule
    schedule = Schedule("schedule")
    schedule.addTask(resources["bedroomLightsOnSunset"])
    schedule.addTask(resources["bedroomLightsOffSunrise"])
    schedule.addTask(resources["porchLightsOnSunset"])
    schedule.addTask(resources["outsideLightsOffMidnight"])
    schedule.addTask(resources["outsideLightsOffSunrise"])
    schedule.addTask(resources["xmasLightsOnSunset"])
    schedule.addTask(resources["xmasLightsOffMidnight"])
    schedule.addTask(resources["xmasLightsOffSunrise"])
#        schedule.addTask(resources["xmasTreeOnXmas"])
    schedule.start()

    # start the task to transmit resource metrics
    resourceStates = ResourceStateSensor("states", None, resources=resources, event=stateChangeEvent)
    startMetrics(resourceStates)

    # start the cache to listen for services on other servers
    restCache = RestProxy("restProxy", resources, watch=restWatch, ignore=restIgnore, event=stateChangeEvent)
    restCache.start()

    # monitor service states
    watchServices(resources, serviceMonitorNotifyNumbers)

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
