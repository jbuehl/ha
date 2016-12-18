webPort = 80
webSSLPort = 7380
webSSLDomain = "cloud.buehltech.com"
webUpdateInterval = 1
webPageTitle = "Home Automation Test"
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
from ha.haWeb import *

# global variables
templates = None
resources = None
stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

# default - dashboard                
def index():
    debug('debugWeb', "/")
    with resourceLock:
        timeGroup = ["Time", resources.getResList(["theDateDayOfWeek", "theTimeAmPm", "sunrise", "sunset"])]
        weatherGroup = ["Weather", resources.getResList(["deckTemp", "humidity", "barometer"])]
        poolGroup = ["Pool", resources.getResList(["spaTemp", "poolPump", "poolPumpFlow", "spaFill", "spaFlush", "spaDrain", "filter", "clean", "flush"])]
        lightsGroup = ["Lights", resources.getResList(["porchLights", "frontLights", "backLights", "bedroomLight", "bathroomLight", "poolLight", "spaLight"])]
        shadesGroup = ["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])]
        hvacGroup = ["Hvac", resources.getResList(["kitchenTemp", "southHeatTempTarget", "southCoolTempTarget", "familyRoomDoor", 
                                                   "masterBedroomTemp", "northHeatTempTarget", "northCoolTempTarget", "masterBedroomDoor"])]
        sprinklersGroup = ["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "backBedSequence", "frontLawnSequence"])]
        powerGroup = ["Power", resources.getResList(["currentVoltage", "currentLoad", "currentPower", "todaysEnergy"])]
        reply = templates.get_template("dashboard.html").render(script="",
                            groupTemplate=templates.get_template("group.html"),
                            resourceTemplate=templates.get_template("resource.html"),
                            timeGroup=timeGroup,
                            weatherGroup=weatherGroup,
                            poolGroup=poolGroup,
                            lightsGroup=lightsGroup,
                            shadesGroup=shadesGroup,
                            hvacGroup=hvacGroup,
                            sprinklersGroup=sprinklersGroup,
                            powerGroup=powerGroup,
                            views=views)
    return reply
    
# show all resource details or specified group                
def details(group=None):
    debug('debugWeb', "/detail", group)
    try:
        groups = [group.capitalize()]
        details = False
    except:
        groups = ["Time", "Temperature", "Hvac", "Pool", "Lights", "Shades", "Doors", "Water", "Power", "Solar", "Inverters", "Optimizers", "Cameras", "Services", "Tasks"]
        details = True
    with resourceLock:
        reply = templates.get_template("details.html").render(title=webPageTitle, script="", 
                            groupTemplate=templates.get_template("group.html"),
                            resourceTemplate=templates.get_template("resource.html"),
                            groups=[[group, resources.getGroup(group)] for group in groups],
                            views=views,
                            details=details)
    return reply
    
# Solar   
def solar():
    debug('debugWeb', "/solar", cherrypy.request.method)
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
def ipad():
    debug('debugWeb', "/ipad", cherrypy.request.method)
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
def iphone5():
    debug('debugWeb', "/iphone5", cherrypy.request.method)
    with resourceLock:
        reply = templates.get_template("iphone5.html").render(script="", 
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            temp=resources.getRes(outsideTemp),
                            resources=resources.getResList(["spaTemp",
                                                            "porchLights", 
                                                            "shade1", "shade2", "shade3", "shade4", 
                                                            "backLawnSequence", "backBedSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence",
                                                            "poolPump"]),
                            views=views)
    return reply

# iPhone 3GS - 320x480    
def iphone3gs():
    debug('debugWeb', "/iphone3gs", cherrypy.request.method)
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
            "details": details,
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
    resources.addRes(HASensor("theDateDayOfWeek", timeInterface, "%A %B %d %Y", type="date", group="Time", label="Date"))
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
    resources.addRes(ControlGroup("porchLights", ["frontLights",
                                               "backLights",
                                               "garageBackDoorLight"],
                                               resources=resources, 
                                               group="Lights", label="Porch lights"))
    resources.addRes(ControlGroup("xmasLights", ["xmasTree",
                                            "xmasCowTree",
                                            "xmasFrontLights",
                                            "xmasBackLights"],
                                               resources=resources, 
                                               group="Lights", label="Xmas lights"))
    resources.addRes(ControlGroup("outsideLights", ["porchLights",
                                               "bbqLights",
                                               "backYardLights",
                                               "deckLights",
                                               "trashLights",
                                               "xmasFrontLights",
                                               "xmasBackLights"],
                                               resources=resources, 
                                               group="Lights", label="Outside lights"))
    resources.addRes(ControlGroup("bedroomLights", ["bedroomLight", 
                                               "bathroomLight"],
                                               resources=resources, 
                                               stateList=[[0, 100, 0], [0, 100, 10]], 
                                               type="nightLight", group="Lights", label="Night lights"))

    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    templates = Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates')))
    webInit(resources, restCache, stateChangeEvent, resourceLock, httpPort=webPort, pathDict=pathDict, baseDir=baseDir, block=True)
    
