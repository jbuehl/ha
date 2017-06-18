webPort = 80
webSSLPort = 7380
webSSLDomain = "cloud.buehltech.com"
webUpdateInterval = 1
webPageTitle = "Home Automation"
runRestServer = False
restIgnore = []
restPort = 7378
insideTemp = "diningRoomTemp"
outsideTemp = "poolEquipTemp"
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
        screenWidth = 1280
        labelWidth = 180
        columnWidth = screenWidth/2
        columnWidths = [columnWidth, [labelWidth, 200, 260]]
        widths = [screenWidth, [columnWidths, columnWidths]]
        timeGroup = ["Time", resources.getResList(["theDateDayOfWeek", "theTimeAmPm", "sunrise", "sunset"])]
        weatherGroup = ["Weather", resources.getResList([outsideTemp, "humidity", "barometer"])]
        poolGroup = ["Pool", resources.getResList(["spaFill", "spaFlush", "spaDrain", 
                                                    "filterSequence", "cleanSequence", "flushSequence"])]
        lightsGroup = ["Lights", resources.getResList(["porchLights", "frontLights", "backLights", "bedroomLights", 
#                                                       "xmasLights", "xmasTree",
                                                       "poolLight", "spaLight"])]
        shadesGroup = ["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])]
        southHvac = templates.get_template("hvacControl.html").render(label="Living area",
                            widths=columnWidths,
                            templates=templates,
                            tempSensor=resources.getRes("diningRoomTemp"), 
                            heatTargetControl=resources.getRes("southHeatTempTarget"), 
                            coolTargetControl=resources.getRes("southCoolTempTarget"), 
                            thermostatControl=resources.getRes("southThermostat"), 
                            thermostatUnitSensor=resources.getRes("southThermostatUnitSensor"),
                            views=views)
        northHvac = templates.get_template("hvacControl.html").render(label="Bedrooms",
                            widths=columnWidths,
                            templates=templates,
                            tempSensor=resources.getRes("masterBedroomTemp"), 
                            heatTargetControl=resources.getRes("northHeatTempTarget"), 
                            coolTargetControl=resources.getRes("northCoolTempTarget"), 
                            thermostatControl=resources.getRes("northThermostat"), 
                            thermostatUnitSensor=resources.getRes("northThermostatUnitSensor"),
                            views=views)
        backHvac = templates.get_template("hvacControl.html").render(label="Back house",
                            widths=columnWidths,
                            templates=templates,
                            tempSensor=resources.getRes("backHouseTemp"), 
                            heatTargetControl=resources.getRes("backHeatTempTarget"), 
                            coolTargetControl=resources.getRes("backCoolTempTarget"), 
                            thermostatControl=resources.getRes("backThermostat"), 
                            thermostatUnitSensor=resources.getRes("backThermostatUnitSensor"),
                            views=views)
        sprinklersGroup = ["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "backBedSequence", "frontLawnSequence"])]
        powerGroup = templates.get_template("powerWidget.html").render(
                            widths=[columnWidth, labelWidth],
                            templates=templates,
                            power=resources["currentPower"],
                            load=resources["currentLoad"],
                            voltage=resources["currentVoltage"],
                            energy=resources["todaysEnergy"],
                            lifetime=resources["lifetimeEnergy"],
                            views=views)
        reply = templates.get_template("dashboard.html").render(script="",
                            templates=templates,
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
                            hvac=southHvac+northHvac+backHvac,
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
        screenWidth = 1280
        labelWidth = 220
        widths = [screenWidth, [labelWidth, 160, 260, 120, 100, 120, 240, 60]]
        reply = templates.get_template("details.html").render(title=webPageTitle, script="", 
                            templates=templates,
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
        screenWidth = 1024
        labelWidth = 180
        columnWidth = screenWidth/2
        columnWidths = [columnWidth, [labelWidth, 140, 192]]
        headerWidths = [screenWidth, [62, 58, 312, 200, 200, 180]]
        widths = [screenWidth, [columnWidths, columnWidths]]
        widths = [headerWidths, [screenWidth, [columnWidths, columnWidths]]]
        southHvac = templates.get_template("hvacControl.html").render(label="Inside temp",
                            widths=columnWidths,
                            templates=templates,
                            tempSensor=resources.getRes("diningRoomTemp"), 
                            heatTargetControl=resources.getRes("southHeatTempTarget"), 
                            coolTargetControl=resources.getRes("southCoolTempTarget"), 
                            thermostatUnitSensor=resources.getRes("southThermostatUnitSensor"),
                            views=views)
        reply = templates.get_template("ipad.html").render(script="", 
                            templates=templates,
                            widths=widths,
                            time=resources.getRes("theTime"),
                            ampm=resources.getRes("theAmPm"),
                            day=resources.getRes("theDay"),
                            pooltemp=resources.getRes("poolTemp"),
                            outtemp=resources.getRes(outsideTemp),
                            humidity=resources.getRes("humidity"),
                            spa=resources.getRes("spa"),
                            spaTemp=resources.getRes("spaTemp"),
                            spaTempTarget=resources.getRes("spaTempTarget"),
                            lightsGroup=["Lights", resources.getResList(["porchLights", "poolLight", "spaLight"])], 
#                           xmasGroup=["Lights", resources.getResList(["porchLights", "xmasLights", "xmasTree"])], 
#                                      ["Lights", resources.getResList(["bbqLights", "backYardLights"])], 
#                                      ["Lights", resources.getResList(["xmasTree", "xmasCowTree", "xmasLights"])], 
                            shadesGroup=["Shades", resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])], 
                            hvac=southHvac, 
                            sprinklersGroup=["Sprinklers", resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"])],
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
        northHvac = templates.get_template("hvacControl.html").render(label="Temperature",
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
 
