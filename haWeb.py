import os
import cherrypy
import json
import threading
import time
from jinja2 import Environment, FileSystemLoader
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.timeInterface import *

# transform functions for views
def ctof(tempc):
    return tempc*9/5+23

def kilo(value):
    return value/1000.0
    
def mega(value):
    return value/1000000.0

def seqCountdown(resource):
    pass
    
# view definitions    
views = {"power": HAView({}, "%d W"),
         "tempC": HAView({}, "%d F", ctof),
         "tempF": HAView({}, "%d F"),
         "door": HAView({0:"Closed", 1:"Open"}, "%s"),
         "shade": HAView({None:"", 0:"Up", 1:"Down", 2:"Raising", 3:"Lowering"}, "%s", None, {0:"Up", 1:"Down"}),
         "spa": HAView({0:"Off", 1:"On", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}, "%s", None, {0:"Off", 1:"On", 4:"Stby"}),
         "poolValves": HAView({0:"Pool", 1:"Spa"}, "%s", None, {0:"Pool", 1:"Spa"}),
         "pump": HAView({0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}, "%s", None, {0:"Off", 1:"Lo", 2:"Med", 3:"Hi", 4:"Max"}),
         "pumpSpeed": HAView({}, "%d RPM"),
         "pumpFlow": HAView({}, "%d GPM"),
         "cleaner": HAView({0:"Off", 1:"On", 2:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "heater": HAView({0:"Off", 1:"On", 4:"Ena"}, "%s", None, {0:"Off", 1:"On"}),
         "KVA": HAView({}, "%7.3f KVA", kilo),
         "KW": HAView({}, "%7.3f KW", kilo),
         "KWh": HAView({}, "%7.3f KWh", kilo),
         "MWh": HAView({}, "%7.3f MWh", mega),
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
                            
class WebRoot(object):
    def __init__(self, resources, env):
        self.resources = resources
        self.env = env
    
    # Everything    
    @cherrypy.expose
    def index(self, action=None, resource=None):
        if debugWeb: log("/", "get", action, resource)
        # lock.acquire()
        reply = self.env.get_template("default.html").render(title="4319 Shadyglade", script="", 
                            groups=[[group, self.resources.getGroup(group)] for group in ["Time", "Temperature", "Pool", "Lights", "Doors", "Water", "Solar", "Power", "Tasks"]],
                            buttons=buttons)
        # lock.release()
        return reply

    # Submit    
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        if debugWeb: log("/submit", "post", action, resource)
        self.resources[resource].setViewState(action)
        reply = ""
        return reply

    # iPad - 1024x768   
    @cherrypy.expose
    def ipad(self, action=None, resource=None):
        if debugWeb: log("/ipad", "get", action, resource)
        # lock.acquire()
        groups = [["Pool", self.resources.getResList(["poolPump", "clean1hr", "spa", "poolTemp", "spaTemp"])], 
                  ["Lights", self.resources.getResList(["frontLights", "backLights", "bbqLights", "backYardLights", "poolLight", "spaLight"])], 
                  ["Shades", self.resources.getResList(["shade1", "shade2", "shade3", "shade4"])], 
                  ["Sprinklers", self.resources.getResList(["backLawnSequence", "sideBedSequence", "frontLawnSequence"])]
                  ]
        reply = self.env.get_template("ipad.html").render(script="", 
                            time=self.resources["theTime"],
                            ampm=self.resources["theAmPm"],
                            day=self.resources["theDay"],
                            temp=self.resources["airTemp"],
                            groups=groups,
                            buttons=buttons)
        # lock.release()
        return reply

    # iPhone 3GS - 320x480    
    @cherrypy.expose
    def iphone3gs(self, action=None, resource=None):
        if debugWeb: log("/iphone3gs", "get", action, resource)
        # lock.acquire()
        resources = self.resources.getResList(["frontLights", "backLights", "bedroomLight", "recircPump"])
        reply = self.env.get_template("iphone3gs.html").render(script="", 
                            time=self.resources["theTime"],
                            ampm=self.resources["theAmPm"],
                            day=self.resources["theDay"],
                            temp=self.resources["airTemp"],
                            resources=resources,
                            buttons=buttons)
        # lock.release()
        return reply

    # Solar    
    @cherrypy.expose
    def solar(self):
        return self.env.get_template("group.html").render(title="Solar", css="solar.css", 
                            resources=self.resources.getResList(["currentPower", "todaysEnergy", "lifetimeEnergy"]), 
                            buttons=buttons)

    # Lights    
    @cherrypy.expose
    def lights(self, action=None, resource=None, link=None):
        if resource:
            self.resources[resource].setViewState(action)
        return self.env.get_template("group.html").render(title="Lights", css="lights.css", 
                            resources=self.resources.getResList(["frontLights", "backLights", "bbqLights", "backYardLights", "poolLight", "spaLight", "xmasLights"]), 
                            buttons=buttons)

    # Pool    
    @cherrypy.expose
    def pool(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action)
        return self.env.get_template("group.html").render(title="Pool", css="pool.css", 
                            resources=self.resources.getResList(["poolTemp", "cleanMode", "poolPump", "poolCleaner", "poolLight", "spaLight"]), 
                            buttons=buttons)

    # Spa    
    @cherrypy.expose
    def spa(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action)
        return self.env.get_template("group.html").render(title="Spa", css="spa.css", 
                            resources=self.resources.getResList(["poolTemp", "spaTemp", "spaWarmup", "spaReady", "spaShutdown", "spaBlower", "poolLight", "spaLight"]), 
                            buttons=buttons)

    # Sprinklers    
    @cherrypy.expose
    def sprinklers(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action)
        return self.env.get_template("group.html").render(title="Sprinklers", css="sprinklers.css", 
                            resources=self.resources.getResList(["frontLawnSequence", "gardenSequence", "backLawnSequence", "sideBedSequence"]), 
                            buttons=buttons)

    # Doors    
    @cherrypy.expose
    def doors(self, action=None, resource=None):
        if resource:
            self.resources[resource].setViewState(action)
        return self.env.get_template("group.html").render(title="Doors", css="doors.css", 
                            resources=self.resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"]), 
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
    def update(self, _=None):
        # types whose class does not depend on their value
        staticTypes = ["time", "ampm", "date", "tempF"]
        updates = {}
        if webUpdateStateChange:
            stateChangeEvent.clear()
            if debugInterrupt: log("update", "event clear", stateChangeEvent)
            stateChangeEvent.wait()
            if debugInterrupt: log("update", "event wait", stateChangeEvent)
        # lock.acquire()
        for resource in self.resources:
            if self.resources[resource].name != "states":
                try:
                    resClass = self.resources[resource].type
                    resState = self.resources[resource].getViewState()
                    if resClass not in staticTypes:
                        resClass += "_"+resState
                    updates[resource] = (resClass, resState)
                except:
                    pass
        # lock.release()
        return json.dumps(updates)        

# Rest client thread.
class RestClient(threading.Thread):

    def __init__(self, name, resources, restInterfaces, selfRest=""):
        threading.Thread.__init__(self, target=self.doRest)
        self.name = name
        self.servers = {}
        self.resources = resources
        self.restInterfaces = restInterfaces
        self.selfRest = selfRest
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("", 4242))
                
    def doRest(self):
        if debugThread: log(self.name, "started")
        while running:
            # loop until the program state changes to not running
            (data, addr) = self.socket.recvfrom(4096)
            #log ("beacon data", data)
            server = json.loads(data)
            serverName = server[0]+":"+str(server[1])
            serverAddr = addr[0]+":"+str(server[1])
            serverResources = server[2]
            if serverName != self.selfRest:   # ignore the beacon from this service
                if serverAddr not in self.servers.values():
                    # lock.acquire()
                    restInterface = HARestInterface(serverName, server=serverAddr, event=stateChangeEvent, secure=False)
                    self.restInterfaces.append(restInterface)
                    resources.load(restInterface, "/"+serverResources["name"])
                    resources.addViews(views)
                    # fill the cache
                    restInterface.readStates()
                    # lock.release()
                    self.servers[serverName] = serverAddr
        if debugThread: log(self.name, "terminated")


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
    restInterfaces = []
    restClient = RestClient("restClient", resources, restInterfaces, socket.gethostname()+":"+str(webRestPort))
    restClient.start()
    
#    # start the process to get sensor states
#    stateClient = StateClient("stateClient", resources, restInterfaces)
#    stateClient.start()
    
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

