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

class PathHandler(object):
    def __init__(self, resources, env, cache, stateChangeEvent, resourceLock):
        self.resources = resources
        self.env = env
        self.cache = cache
        self.stateChangeEvent = stateChangeEvent
        self.resourceLock = resourceLock
        self.pathDict = {"": self.index,
                         "solar": self.solar,
                         "ipad": self.ipad,
                         "iphone5": self.iphone5,
                         "iphone3gs": self.iphone3gs,
                         }

   # default - show all resources or specified group                
    def index(self, group=None):
        debug('debugWeb', "/", group)
        try:
            groups = [group.capitalize()]
            details = False
        except:
            groups = ["Time", "Temperature", "Hvac", "Pool", "Lights", "Shades", "Doors", "Water", "Solar", "Power", "Cameras", "Services", "Tasks"]
            details = True
        with self.resourceLock:
            reply = self.env.get_template("default.html").render(title=webPageTitle, script="", 
                                groups=[[group, self.resources.getGroup(group)] for group in groups],
                                views=views,
                                details=details)
        return reply
        
    # Solar   
    def solar(self, action=None, resource=None):
        debug('debugWeb', "/solar", cherrypy.request.method, action, resource)
        with self.resourceLock:
            reply = self.env.get_template("solar.html").render(script="",
                                dayOfWeek=self.resources.getRes("theDayOfWeek"),
                                date=self.resources.getRes("theDate"),
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                sunrise=self.resources.getRes("sunrise"),
                                sunset=self.resources.getRes("sunset"),
                                latitude="%7.3f "%(abs(latLong[0])+.0005)+("N" if latLong[0]>0 else "S"), 
                                longitude="%7.3f "%(abs(latLong[1])+.0005)+("E" if latLong[1]>0 else "W"), 
                                elevation="%d ft"%(elevation),
                                airTemp=self.resources.getRes(outsideTemp),
                                inverterTemp=self.resources.getRes("inverterTemp"), 
                                roofTemp=self.resources.getRes("roofTemp"), 
                                currentVoltage=self.resources.getRes("currentVoltage"), 
                                currentLoad=self.resources.getRes("currentLoad"), 
                                currentPower=self.resources.getRes("currentPower"), 
                                todaysEnergy=self.resources.getRes("todaysEnergy"), 
                                lifetimeEnergy=self.resources.getRes("lifetimeEnergy"), 
                                inverters=self.resources.getGroup("Inverters"), 
                                invertersEnergy=self.resources.getGroup("InvertersEnergy"), 
                                optimizers=self.resources.getGroup("Optimizers"), 
                                optimizersEnergy=self.resources.getGroup("OptimizersEnergy"), 
                                views=views)
        return reply

    # iPad - 1024x768   
    def ipad(self, action=None, resource=None):
        debug('debugWeb', "/ipad", cherrypy.request.method, action, resource)
        with self.resourceLock:
            reply = self.env.get_template("ipad.html").render(script="", 
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                day=self.resources.getRes("theDay"),
                                pooltemp=self.resources.getRes(poolTemp),
                                intemp=self.resources.getRes(insideTemp),
                                outtemp=self.resources.getRes(outsideTemp),
                                groups=[["Pool", self.resources.getResList(["spaTemp"])], 
                                      ["Lights", self.resources.getResList(["porchLights", "poolLight", "spaLight"])], 
#                                      ["Lights", self.resources.getResList(["bbqLights", "backYardLights"])], 
#                                      ["Lights", self.resources.getResList(["xmasTree", "xmasCowTree", "xmasLights"])], 
                                      ["Shades", self.resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])], 
                                      ["Hvac", self.resources.getResList(["southHeatTempTarget", "southCoolTempTarget", "northHeatTempTarget", "northCoolTempTarget"])], 
                                      ["Sprinklers", self.resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"])]
                                      ],
                                views=views)
        return reply

    # iPhone 5 - 320x568    
    def iphone5(self, action=None, resource=None):
        debug('debugWeb', "/iphone5", cherrypy.request.method, action, resource)
        with self.resourceLock:
            reply = self.env.get_template("iphone5.html").render(script="", 
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                temp=self.resources.getRes(outsideTemp),
                                resources=self.resources.getResList(["spaTemp", "porchLights", "allShades", "shade1", "shade2", "shade3", "shade4", "backLawnSequence", "backBedSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"]),
                                views=views)
        return reply

    # iPhone 3GS - 320x480    
    def iphone3gs(self, action=None, resource=None):
        debug('debugWeb', "/iphone3gs", cherrypy.request.method, action, resource)
        with self.resourceLock:
            reply = self.env.get_template("iphone3gs.html").render(script="", 
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                day=self.resources.getRes("theDay"),
                                temp=self.resources.getRes(outsideTemp),
                                resources=self.resources.getResList(["porchLights", "xmasLights", "bedroomLights", "recircPump", "garageDoors", "houseDoors"]),
                                views=views)
        return reply

if __name__ == "__main__":
    # initialize resources
    try:
        with open(rootDir+"aliases") as aliasFile:
            aliases = json.load(aliasFile)
    except:
        aliases = {}
    resources = HACollection("resources", aliases=aliases)
    stateChangeEvent = threading.Event()
    resourceLock = threading.Lock()

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
    pathHandler = PathHandler(resources, Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates'))), restCache, stateChangeEvent, resourceLock)
    webInit(resources, restCache, stateChangeEvent, resourceLock, httpPort=webPort, ssl=True, httpsPort=webSSLPort, domain=webSSLDomain, pathDict=pathHandler.pathDict, baseDir=baseDir)
    
    # start the REST server for this service
    restServer = RestServer(resources, port=webRestPort, event=stateChangeEvent)
    # restServer.start()
    while True:
        time.sleep(1)

