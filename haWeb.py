# coding=utf-8

import os
import cherrypy
import json
import threading
import time
from jinja2 import Environment, FileSystemLoader
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.restCache import *
from ha.timeInterface import *

# transform functions for views
def ctofFormat(value):
    return value*9/5+32

def kiloFormat(value):
    return value/1000.0
    
def megaFormat(value):
    return value/1000000.0

def seqCountdownFormat(resource):
    pass

def tempFormat(value):
    if value == 0:
        return "--"
    else:
        return "%d F"%(value)
        
def spaTempFormat(value):
    temp = int(str(value).split(" ")[0])
    try:
        state = int(str(value).split(" ")[1])
    except:
        state = 0
    if temp == 0:
        return "Off"
    else:
        return "%d F %s" % (temp, {0:"Off", 1:"Ready", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}[state])
        
# view definitions    
views = {"power": HAView({}, "%d W"),
#         "tempC": HAView({}, "%d °", ctofFormat),
#         "tempF": HAView({}, "%d °", tempFormat),
         "tempC": HAView({}, "%d F", ctofFormat),
         "tempF": HAView({}, "%d F", tempFormat),
         "barometer": HAView({}, "%5.2f in"),
         "humidity": HAView({}, "%d %%"),
         "door": HAView({0:"Closed", 1:"Open"}, "%s"),
         "shade": HAView({None:"", 0:"Up", 1:"Down", 2:"Raising", 3:"Lowering"}, "%s", None, {0:"Up", 1:"Down"}),
         "spa": HAView({0:"Off", 1:"On", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}, "%s", None, {0:"Off", 1:"On", 4:"Stby"}),
         "spaTemp": HAView({}, "%s", spaTempFormat, {0:"Off", 1:"On"}),
         "poolValves": HAView({0:"Pool", 1:"Spa"}, "%s", None, {0:"Pool", 1:"Spa"}),
         "pump": HAView({0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}, "%s", None, {0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}),
         "pumpSpeed": HAView({}, "%d RPM"),
         "pumpFlow": HAView({}, "%d GPM"),
         "cleaner": HAView({0:"Off", 1:"On", 2:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "heater": HAView({0:"Off", 1:"On", 4:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "cameraMode": HAView({0:"Still", 1:"Video", 2:"Motion"}, "%s", None, {0:"Still", 1:"Video", 2:"Motion"}),
         "cameraEnable": HAView({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"}),
         "cameraRecord": HAView({0:"Stopped", 1:"Recording"}, "%s", None, {0:"Stop", 1:"Rec"}),
         "KVA": HAView({}, "%7.3f KVA", kiloFormat),
         "KW": HAView({}, "%7.3f KW", kiloFormat),
         "KWh": HAView({}, "%7.3f KWh", kiloFormat),
         "MWh": HAView({}, "%7.3f MWh", megaFormat),
         "sequence": HAView({0:"Stopped", 1:"Running"}, "%s", None, {0:"Stop", 1:"Run"}),
         "task": HAView({0:"Disabled", 1:"Enabled"}, "%s", None, {0:"Dis", 1:"Ena"})
         }

buttons = [] #"index", "solar", "lights", "pool", "spa", "sprinklers", "doors"]

pageResources = {"index": [],
                 "ipad": [],
                 "iphone3gs": [],
                 "": [],
                }

stateChangeEvent = threading.Event()
resourceLock = threading.Lock()

# set temp color based on temp value
def tempColor(tempString):
    try:
        temp = int(tempString.split(" ")[0])
    except:
        temp = 0       
    if temp > 120:                 # magenta
        red = 252
        green = 0
        blue = 252
    elif temp > 102:               # red
        red = 252
        green = 0
        blue = (temp-102)*14
    elif temp > 84:                # yellow
        red = 252
        green = (102-temp)*14
        blue = 0
    elif temp > 66:                # green
        red = (temp-66)*14
        green = 252
        blue = 0
    elif temp > 48:                # cyan
        red = 0
        green = 252
        blue = (66-temp)*14
    elif temp > 30:                # blue
        red = 0
        green = (temp-30)*14
        blue = 252
    elif temp > 0:
        red = 0
        green = 0
        blue = 252
    else:
        red = 112
        green = 128
        blue = 144
    return 'rgb('+str(red)+','+str(green)+','+str(blue)+')'
                            
class WebRoot(object):
    def __init__(self, resources, env):
        self.resources = resources
        self.env = env
    
    # Everything    
    @cherrypy.expose
    def index(self, action=None, resource=None):
        debug('debugWeb', "/", "get", action, resource)
        with resourceLock:
            reply = self.env.get_template("default.html").render(title="4319 Shadyglade", script="", 
                                groups=[[group, self.resources.getGroup(group)] for group in ["Time", "Temperature", "Pool", "Lights", "Doors", "Water", "Solar", "Power", "Cameras", "Tasks"]],
                                views=views,
                                buttons=buttons)
        return reply

    # Submit    
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        debug('debugWeb', "/submit", "post", action, resource)
        self.resources[resource].setViewState(action, views)
        reply = ""
        return reply

    # iPad - 1024x768   
    @cherrypy.expose
    def ipad(self, action=None, resource=None):
        debug('debugWeb', "/ipad", "get", action, resource)
        with resourceLock:
            groups = [["Pool", self.resources.getResList(["poolTemp", "spa1"])], 
                      ["Lights", self.resources.getResList(["frontLights", "backLights", "bbqLights", "backYardLights", "poolLight", "spaLight"])], 
                      ["Shades", self.resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])], 
                      ["Sprinklers", self.resources.getResList(["backLawnSequence", "gardenSequence", "sideBedSequence", "frontLawnSequence"])]
                      ]
            reply = self.env.get_template("ipad.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                day=self.resources["theDay"],
                                temp=self.resources["deckTemp"],
                                groups=groups,
                                views=views,
                                buttons=buttons)
        return reply

    # iPhone 5 - 320x568    
    @cherrypy.expose
    def iphone5(self, action=None, resource=None):
        debug('debugWeb', "/iphone5", "get", action, resource)
        with resourceLock:
            resources = self.resources.getResList(["spa1", "frontLights", "backLights", "allShades", "shade1", "shade2", "shade3", "shade4", "backLawn", "backBeds", "garden", "sideBeds", "frontLawn"])
            reply = self.env.get_template("iphone5.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                temp=self.resources["deckTemp"],
                                resources=resources,
                                views=views,
                                buttons=buttons)
        return reply

    # iPhone 3GS - 320x480    
    @cherrypy.expose
    def iphone3gs(self, action=None, resource=None):
        debug('debugWeb', "/iphone3gs", "get", action, resource)
        with resourceLock:
            resources = self.resources.getResList(["frontLights", "backLights", "bedroomLight", "recircPump", "garageBackDoor"])
            reply = self.env.get_template("iphone3gs.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                day=self.resources["theDay"],
                                temp=self.resources["deckTemp"],
                                resources=resources,
                                views=views,
                                buttons=buttons)
        return reply

    # Solar    
    @cherrypy.expose
    def solar(self):
        return self.env.get_template("group.html").render(title="Solar", css="solar.css", 
                            resources=self.resources.getResList(["currentPower", "todaysEnergy", "lifetimeEnergy"]), 
                            views=views,
                            buttons=buttons)

    # Lights    
    @cherrypy.expose
    def lights(self, action=None, resource=None, link=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Lights", css="lights.css", 
                            resources=self.resources.getResList(["frontLights", "backLights", "bbqLights", "backYardLights", "poolLight", "spaLight", "xmasLights"]), 
                            views=views,
                            buttons=buttons)

    # Pool    
    @cherrypy.expose
    def pool(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Pool", css="pool.css", 
                            resources=self.resources.getResList(["poolTemp", "cleanMode", "poolPump", "poolCleaner", "poolLight", "spaLight"]), 
                            views=views,
                            buttons=buttons)

    # Spa    
    @cherrypy.expose
    def spa(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Spa", css="spa.css", 
                            resources=self.resources.getResList(["poolTemp", "spaTemp", "spaWarmup", "spaReady", "spaShutdown", "spaBlower", "poolLight", "spaLight"]), 
                            views=views,
                            buttons=buttons)

    # Sprinklers    
    @cherrypy.expose
    def sprinklers(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Sprinklers", css="sprinklers.css", 
                            resources=self.resources.getResList(["frontLawnSequence", "gardenSequence", "backLawnSequence", "sideBedSequence"]), 
                            views=views,
                            buttons=buttons)

    # Doors    
    @cherrypy.expose
    def doors(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action, views)
        return self.env.get_template("group.html").render(title="Doors", css="doors.css", 
                            resources=self.resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"]), 
                            views=views,
                            buttons=buttons)

    # Return the value of a resource attribute
    @cherrypy.expose
    def value(self, resource=None, attr=None):
        try:
            if resource:
                if attr:
                    return self.resources[resource].__getattribute__(attr).__str__()
                else:
                    return self.resources[resource].dict().__str__()
        except:
            return "Error"        

    # Update the states of all resources
    @cherrypy.expose
    def state(self, _=None):
        return self.update( self.resources)
        
    # Update the states of resources that have changed
    @cherrypy.expose
    def stateChange(self, _=None):
        debug('debugInterrupt', "update", "event wait")
        stateChangeEvent.wait()
        debug('debugInterrupt', "update", "event clear")
        stateChangeEvent.clear()
        return self.update(self.resources)

    # Update the states of the specified resources
    def update(self, resources):
        staticTypes = ["time", "ampm", "date"]          # types whose class does not depend on their value
        tempTypes = ["tempF", "tempC", "spaTemp"]       # temperatures
        updates = {}
        with resourceLock:
            for resource in resources:
                if self.resources[resource].name != "states":
                    try:
                        resState = self.resources[resource].getViewState(views)
                        resClass = self.resources[resource].type
                        if resClass in tempTypes:
                            updates[resource] = ("temp", resState, tempColor(resState))
                        else:
                            if resClass not in staticTypes:
                                resClass += "_"+resState
                            updates[resource] = (resClass, resState, "")
                    except:
                        pass
        return json.dumps(updates)        


if __name__ == "__main__":

    # resources
    resources = HACollection("resources")

    # time resources
    timeInterface = TimeInterface("time")
    resources.addRes(HASensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(HASensor("theDate", timeInterface, "%B %d %Y", type="date", group="Time", label="Date"))
    resources.addRes(HASensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(HASensor("theDay", timeInterface, "%a %B %d %Y", type="date", label="Day"))
    resources.addRes(HASensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(HASensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    # start the process to listen for services
    restCache = RestCache("restCache", resources, socket.gethostname()+":"+str(webRestPort), stateChangeEvent, resourceLock)
    restCache.start()
    
    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    globalConfig = {
        'server.socket_port': webPort,
        'server.socket_host': "0.0.0.0",
        }
    appConfig = {
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "css",
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "js",
        },
        '/favicon.ico': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(baseDir, "static/favicon.ico"),
        },
    }    
    cherrypy.config.update(globalConfig)
    root = WebRoot(resources, Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates'))))
    cherrypy.tree.mount(root, "/", appConfig)
    if not webLogging:
        access_log = cherrypy.log.access_log
        for handler in tuple(access_log.handlers):
            access_log.removeHandler(handler)
    cherrypy.engine.timeout_monitor.unsubscribe()
    cherrypy.engine.autoreload.unsubscribe()
    cherrypy.engine.start()

    # start the REST server for this service
    restServer = RestServer(resources, port=webRestPort, event=stateChangeEvent)
    restServer.start()

