webPort = 80
webSSLPort = 7380
webSSLDomain = "cloud.buehltech.com"
webUpdateInterval = 1
webPageTitle = "Home Automation"
runRestServer = False
restIgnore = []
restPort = 7378
insideTemp = "diningRoomTemp"
outsideTemp = "deckTemp"
poolTemp = "poolTemp"

import time
from jinja2 import Environment, FileSystemLoader
from ha import *
from ha.interfaces.restInterface import *
from ha.interfaces.timeInterface import *
from ha.rest.restServer import *
from ha.rest.restProxy import *
from ha.ui.webUI import *

# global variables
templates = None
resources = None
stateChangeEvent = threading.Event()

# default - dashboard                
def index():
    debug('debugWeb', "/")
    with resources.lock:
        widths = [1280, [[640, [180, 200, 260]], [640, [180, 200, 260]]]]
        timeGroup = ["Time", resources.getResList(["theDateDayOfWeek", "theTimeAmPm", "sunrise", "sunset"])]
        weatherGroup = ["Weather", resources.getResList(["deckTemp", "humidity", "barometer"])]
        poolGroup = ["Pool", resources.getResList(["spaFill", "spaFlush", "spaDrain", 
                                                    "filterSequence", "cleanSequence", "flushSequence"])]
        lightsGroup = ["Lights", resources.getResList(["porchLights", "frontLights", "backLights", "bedroomLights", 
#                                                       "xmasLights", "xmasTree",
                                                       "poolLight", "spaLight"])]
        shadesGroup = ["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])]
        hvacGroup = ["Hvac", resources.getResList(["diningRoomTemp", "southHeatTempTarget", "southCoolTempTarget", "southThermostat",
                                                   "masterBedroomTemp", "northHeatTempTarget", "northCoolTempTarget", "northThermostat"])]
        sprinklersGroup = ["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "backBedSequence", "frontLawnSequence"])]
        powerGroup = ["Power", resources.getResList(["currentVoltage", "currentLoad", "currentPower", "todaysEnergy"])]
        reply = templates.get_template("dashboard.html").render(script="",
                            groupTemplate=templates.get_template("group.html"),
                            resourceTemplate=templates.get_template("resource.html"),
                            spaTempTemplate=templates.get_template("spaTemp.html"),
                            poolPumpControlTemplate=templates.get_template("poolPumpControl.html"),
                            widths=widths,
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            poolPumpControl=resources.getRes("poolPump"),
                            poolPumpFlowSensor=resources.getRes("poolPumpFlow"),
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
        groups = ["Time", "Weather", "Temperature", "Hvac", "Pool", "Lights", "Shades", "Doors", 
                  "Sprinklers", "Water", "Power", "Solar", "Inverters", "Optimizers", "Cameras", 
                  "Services", "Tasks"]
        details = True
    with resources.lock:
        widths = [1280, [220, 160, 260, 120, 100, 120, 240, 60]]
        reply = templates.get_template("details.html").render(title=webPageTitle, script="", 
                            groupTemplate=templates.get_template("group.html"),
                            resourceTemplate=templates.get_template("resource.html"),
                            widths=widths,
                            groups=[[group, resources.getGroup(group)] for group in groups],
                            views=views,
                            details=details,
                            link=False)
    return reply
    
# Solar   
def solar():
    debug('debugWeb', "/solar", cherrypy.request.method)
    with resources.lock:
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
    with resources.lock:
        widths = [[1024, [62, 58, 292, 200, 200, 200]], [1024, [[512, [180, 140, 192]], [512, [180, 140, 192]]]]]
        reply = templates.get_template("ipad.html").render(script="", 
                            groupTemplate=templates.get_template("group.html"),
                            resourceTemplate=templates.get_template("resource.html"),
                            spaTempTemplate=templates.get_template("spaTemp.html"),
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            pooltemp=resources.getRes(poolTemp),
                            intemp=resources.getRes(insideTemp),
                            outtemp=resources.getRes(outsideTemp),
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            lightsGroup=["Lights", resources.getResList(["porchLights", "poolLight", "spaLight"])], 
#                           xmasGroup=["Lights", resources.getResList(["porchLights", "xmasLights", "xmasTree"])], 
#                                      ["Lights", resources.getResList(["bbqLights", "backYardLights"])], 
#                                      ["Lights", resources.getResList(["xmasTree", "xmasCowTree", "xmasLights"])], 
                            shadesGroup=["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])], 
                            hvacGroup=["Hvac", resources.getResList(["southHeatTempTarget", "southCoolTempTarget", "northHeatTempTarget", "northCoolTempTarget"])], 
                            sprinklersGroup=["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"])],
                            views=views)
    return reply

# iPhone 5 - 320x568    
def iphone5():
    debug('debugWeb', "/iphone5", cherrypy.request.method)
    with resources.lock:
        widths = [[320, [60, 100, 60]], [320, [120, 72, 128]]]
        reply = templates.get_template("iphone5.html").render(script="", 
                            groupTemplate=templates.get_template("group.html"),
                            resourceTemplate=templates.get_template("resource.html"),
                            spaTempTemplate=templates.get_template("spaTemp.html"),
                            poolPumpControlTemplate=templates.get_template("poolPumpControl.html"),
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            temp=resources.getRes(outsideTemp),
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            poolPumpControl=resources.getRes("poolPump"),
                            poolPumpFlowSensor=resources.getRes("poolPumpFlow"),
                            resources=resources.getResList(["porchLights", 
#                                                            "xmasLights", "xmasTree",
                                                            "shade1", "shade2", "shade3", "shade4", 
                                                            "backLawnSequence", "backBedSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"
                                                            ]),
                            views=views)
    return reply

# iPhone 3GS - 320x480    
def iphone3gs():
    debug('debugWeb', "/iphone3gs", cherrypy.request.method)
    with resources.lock:
        widths = [[320, [296, 24]], [320, [240, 80]], [320, [152, 168]]]
        reply = templates.get_template("iphone3gs.html").render(script="", 
                            groupTemplate=templates.get_template("group.html"),
                            resourceTemplate=templates.get_template("resource.html"),
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            temp=resources.getRes(outsideTemp),
                            resources=resources.getResList(["porchLights", 
#                                                            "xmasLights", 
                                                            "bedroomLights", "recircPump", "garageDoors", "houseDoors"]),
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
    resources = Collection("resources", aliases=aliases)

    # add local resources
    timeInterface = TimeInterface("time")
    resources.addRes(Sensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(Sensor("theDateDayOfWeek", timeInterface, "%a %B %-d %Y", type="date", label="Date"))
    resources.addRes(Sensor("theDate", timeInterface, "%B %-d %Y", type="date", group="Time", label="Date"))
    resources.addRes(Sensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(Sensor("sunrise", timeInterface, "sunrise", type="time", group="Time", label="Sunrise"))
    resources.addRes(Sensor("sunset", timeInterface, "sunset", type="time", group="Time", label="Sunset"))
    resources.addRes(Sensor("theDay", timeInterface, "%a %b %-d %Y", type="date", label="Day"))
    resources.addRes(Sensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(Sensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    # start the cache to listen for services on other servers
    restIgnore.append(socket.gethostname()+":"+str(restPort))
    restCache = RestProxy("restProxy", resources, ignore=restIgnore, event=stateChangeEvent)
    restCache.start()
    
    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    templates = Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates')))
    webInit(resources, restCache, stateChangeEvent, httpPort=webPort, 
#            ssl=True, httpsPort=webSSLPort, domain=webSSLDomain, 
            pathDict=pathDict, baseDir=baseDir, block=not runRestServer)

    if runRestServer:
        restServer = RestServer(resources, port=restPort, event=stateChangeEvent, label="Control")
        restServer.start()
 
