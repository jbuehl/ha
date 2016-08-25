webPort = 80
webRestPort = 7478
webSSLPort = 7380
webSSLDomain = "cloud.buehltech.com"
webUpdateInterval = 1
webPageTitle = "Home Automation"
restIgnore = []
insideTemp = "kitchenTemp"
outsideTemp = "deckTemp"
poolTemp = "waterTemp"

import time
from jinja2 import Environment, FileSystemLoader
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.restProxy import *
from ha.timeInterface import *
from haWeb import *

# global variables
templates = None
resources = None
stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

# default - show all resources or specified group                
def index(group=None):
    debug('debugWeb', "/", group)
    try:
        groups = [group.capitalize()]
        details = False
    except:
        groups = ["Time", "Temperature", "Hvac", "Pool", "Lights", "Shades", "Doors", "Water", "Solar", "Power", "Cameras", "Services", "Tasks"]
        details = True
    with resourceLock:
        reply = templates.get_template("default.html").render(title=webPageTitle, script="", 
                            groups=[[group, resources.getGroup(group)] for group in groups],
                            views=views,
                            details=details)
    return reply
    
# Solar   
def solar(action=None, resource=None):
    debug('debugWeb', "/solar", cherrypy.request.method, action, resource)
    with resourceLock:
        reply = templates.get_template("solar.html").render(script="",
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
                            inverterTemp=resources.getRes("inverterTemp"), 
                            roofTemp=resources.getRes("roofTemp"), 
                            currentVoltage=resources.getRes("currentVoltage"), 
                            currentLoad=resources.getRes("currentLoad"), 
                            currentPower=resources.getRes("currentPower"), 
                            todaysEnergy=resources.getRes("todaysEnergy"), 
                            lifetimeEnergy=resources.getRes("lifetimeEnergy"), 
                            inverters=resources.getGroup("Inverters"), 
                            invertersEnergy=resources.getGroup("InvertersEnergy"), 
                            optimizers=resources.getGroup("Optimizers"), 
                            optimizersEnergy=resources.getGroup("OptimizersEnergy"), 
                            views=views)
    return reply

# iPad - 1024x768   
def ipad(action=None, resource=None):
    debug('debugWeb', "/ipad", cherrypy.request.method, action, resource)
    with resourceLock:
        reply = templates.get_template("ipad.html").render(script="", 
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            pooltemp=resources.getRes(poolTemp),
                            intemp=resources.getRes(insideTemp),
                            outtemp=resources.getRes(outsideTemp),
                            groups=[["Pool", resources.getResList(["spaTemp"])], 
                                  ["Lights", resources.getResList(["porchLights", "poolLight", "spaLight"])], 
#                                      ["Lights", resources.getResList(["bbqLights", "backYardLights"])], 
#                                      ["Lights", resources.getResList(["xmasTree", "xmasCowTree", "xmasLights"])], 
                                  ["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])], 
                                  ["Hvac", resources.getResList(["southHeatTempTarget", "southCoolTempTarget", "northHeatTempTarget", "northCoolTempTarget"])], 
                                  ["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"])]
                                  ],
                            views=views)
    return reply

# iPhone 5 - 320x568    
def iphone5(action=None, resource=None):
    debug('debugWeb', "/iphone5", cherrypy.request.method, action, resource)
    with resourceLock:
        reply = templates.get_template("iphone5.html").render(script="", 
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            temp=resources.getRes(outsideTemp),
                            resources=resources.getResList(["spaTemp", "porchLights", "allShades", "shade1", "shade2", "shade3", "shade4", "backLawnSequence", "backBedSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"]),
                            views=views)
    return reply

# iPhone 3GS - 320x480    
def iphone3gs(action=None, resource=None):
    debug('debugWeb', "/iphone3gs", cherrypy.request.method, action, resource)
    with resourceLock:
        reply = templates.get_template("iphone3gs.html").render(script="", 
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            temp=resources.getRes(outsideTemp),
                            resources=resources.getResList(["porchLights", "xmasLights", "bedroomLights", "recircPump", "garageDoors", "houseDoors"]),
                            views=views)
    return reply

# dispatch table
pathDict = {"": index,
            "solar": solar,
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
    resources = HACollection("resources", aliases=aliases)

    # add local resources
    timeInterface = TimeInterface("time")
    resources.addRes(HASensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(HASensor("theDate", timeInterface, "%B %d %Y", type="date", group="Time", label="Date"))
    resources.addRes(HASensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(HASensor("sunrise", timeInterface, "sunrise", type="time", group="Time", label="Sunrise"))
    resources.addRes(HASensor("sunset", timeInterface, "sunset", type="time", group="Time", label="Sunset"))
    resources.addRes(HASensor("theDay", timeInterface, "%a %b %d %Y", type="date", label="Day"))
    resources.addRes(HASensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(HASensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    # start the cache to listen for services on other servers
    restIgnore.append(socket.gethostname()+":"+str(webRestPort))
    restCache = RestProxy("restProxy", resources, restIgnore, stateChangeEvent, resourceLock)
    restCache.start()
    
    # scenes and groups
    resources.addRes(HAScene("porchLights", ["frontLights",
                                               "backLights",
                                               "garageBackDoorLight"],
                                               resources=resources, 
                                               group="Lights", label="Porch lights"))
    resources.addRes(HAScene("xmasLights", ["xmasTree",
                                            "xmasCowTree",
                                            "xmasFrontLights",
                                            "xmasBackLights"],
                                               resources=resources, 
                                               group="Lights", label="Xmas lights"))
    resources.addRes(HAScene("outsideLights", ["porchLights",
                                               "bbqLights",
                                               "backYardLights",
                                               "deckLights",
                                               "trashLights",
                                               "xmasFrontLights",
                                               "xmasBackLights"],
                                               resources=resources, 
                                               group="Lights", label="Outside lights"))
    resources.addRes(HAScene("bedroomLights", ["bedroomLight", 
                                               "bathroomLight"],
                                               resources=resources, 
                                               stateList=[[0, 100, 0], [0, 100, 10]], 
                                               type="nightLight", group="Lights", label="Night lights"))

    # Tasks
    resources.addRes(HATask("bedroomLightsOnSunset", HASchedTime(event="sunset"), "bedroomLights", 1, resources=resources))
    resources.addRes(HATask("bedroomLightsOffSunrise", HASchedTime(event="sunrise"), "bedroomLights", 0, resources=resources))
    resources.addRes(HATask("porchLightsOnSunset", HASchedTime(event="sunset"), "porchLights", 1, resources=resources))
    resources.addRes(HATask("outsideLightsOffMidnight", HASchedTime(hour=[23,0], minute=[00]), "outsideLights", 0, resources=resources))
    resources.addRes(HATask("outsideLightsOffSunrise", HASchedTime(event="sunrise"), "outsideLights", 0, resources=resources))
    resources.addRes(HATask("xmasLightsOnSunset", HASchedTime(event="sunset"), "xmasLights", 1, resources=resources))
    resources.addRes(HATask("xmasLightsOffMidnight", HASchedTime(hour=[23,0], minute=[00]), "xmasLights", 0, resources=resources))
    resources.addRes(HATask("xmasLightsOffSunrise", HASchedTime(event="sunrise"), "xmasLights", 0, resources=resources))
    resources.addRes(HATask("hotWaterRecircOn", HASchedTime(hour=[05], minute=[0]), "recircPump", 1, resources=resources))
    resources.addRes(HATask("hotWaterRecircOff", HASchedTime(hour=[23], minute=[0]), "recircPump", 0, resources=resources))
    
    # Schedule
    schedule = HASchedule("schedule")
    schedule.addTask(resources["bedroomLightsOnSunset"])
    schedule.addTask(resources["bedroomLightsOffSunrise"])
    schedule.addTask(resources["porchLightsOnSunset"])
    schedule.addTask(resources["outsideLightsOffMidnight"])
    schedule.addTask(resources["outsideLightsOffSunrise"])
    schedule.addTask(resources["xmasLightsOnSunset"])
    schedule.addTask(resources["xmasLightsOffMidnight"])
    schedule.addTask(resources["xmasLightsOffSunrise"])
    schedule.addTask(resources["hotWaterRecircOn"])
    schedule.addTask(resources["hotWaterRecircOff"])
    schedule.start()

    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    templates = Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates')))
    webInit(resources, restCache, stateChangeEvent, resourceLock, httpPort=webPort, ssl=True, httpsPort=webSSLPort, domain=webSSLDomain, pathDict=pathDict, baseDir=baseDir)
    
    # start the REST server for this service
    restServer = RestServer(resources, port=webRestPort, event=stateChangeEvent)
    # restServer.start()
    while True:
        time.sleep(1)

