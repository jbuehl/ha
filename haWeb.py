import os
import cherrypy
import json
import threading
from jinja2 import Environment, FileSystemLoader
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.timeInterface import *

beaconPort = 7379

# transform functions for views
def ctof(tempc):
    return tempc*9/5+23

def kilo(value):
    return value/1000.0
    
def mega(value):
    return value/1000000.0
    
# view definitions    
views = {"power": HAView({}, "%d W"),
         "tempC": HAView({}, "%d F", ctof),
         "tempF": HAView({}, "%d F"),
         "door": HAView({0:"Closed", 1:"Open"}, "%s"),
         "shade": HAView({None:"", 0:"Up", 1:"Down", 2:"Raising", 3:"Lowering"}, "%s", None, {0:"Up", 1:"Down"}),
         "spa": HAView({0:"Off", 1:"On", 2:"Starting", 3:"Warming", 4:"Standby", 5:"Stopping"}, "%s", None, {0:"Off", 1:"On", 4:"Stby"}),
         "poolValves": HAView({0:"Pool", 1:"Spa"}, "%s"),
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
             
######################################################################################
# javascript
######################################################################################

def refreshScript(interval):
    script  = "<script type='text/javascript'>\n"
    script += "function refresh() {\n"
    script += "	   location.reload(true)\n"
    script += "}\n"
    script += "window.setInterval('refresh()',"+str(interval*1000)+");\n"
    script += "</script>\n"
    return script

def redirectScript(location, interval):
    script  = "<script type='text/javascript'>\n"
    script += "function redirect() {\n"
    script += "	   location='"+location+"';\n"
    script += "}\n"
    script += "window.setInterval('redirect()',"+str(interval*1000)+");\n"
    script += "</script>\n"
    return script

def updateScript(interval):
    script  = "<script type='text/javascript'>\n"
    script += "$(document).ready(function() {\n"
    script += "    var refreshId = setInterval(function() {\n"
    script += "      $.getJSON( 'update', {}, function(data) {\n"
    script += "        $.each( data, function(key, val) {\n"
    script += "          $('#'+key).text(val[1]);\n"
#    script += "          $('#'+key).attr('class', val[0]+'_'+val[1]);\n"
    script += "          $('#'+key).attr('class', val[0]);\n"
    script += "          });\n"
    script += "        });\n"
    script += "      }, "+str(interval*1000)+");\n"
    script += "    $.ajaxSetup({cache: false});\n"
    script += "    });\n"
    script += "</script>\n"
    return script

class WebRoot(object):
    def __init__(self, resources, env):
        self.resources = resources
        self.env = env
    
    # Everything    
    @cherrypy.expose
    def index(self, action=None, resource=None):
        if debugWeb: log("get", action, resource)
        if resource:
            self.resources[resource].setViewState(action)
            script = redirectScript("/", 5)
        else:
            script = updateScript(30)
        # lock.acquire()
        reply = self.env.get_template("default.html").render(title="4319 Shadyglade", script=script, 
                            groups=[[group, self.resources.getGroup(group)] for group in ["Time", "Temperature", "Pool", "Lights", "Doors", "Water", "Solar", "Power", "Tasks"]],
                            buttons=buttons)
        # lock.release()
        return reply

    # iPad - 1024x768   
    @cherrypy.expose
    def ipad(self, action=None, resource=None):
        if debugWeb: log("get", action, resource)
        if resource:
            self.resources[resource].setViewState(action)
            script = redirectScript("/ipad", 5)
        else:
            script = updateScript(30)
        # lock.acquire()
        groups = [["Pool", self.resources.getResList(["poolPump", "clean1hr", "spa", "poolTemp", "spaTemp"])], 
                  ["Lights", self.resources.getResList(["frontLights", "backLights", "bbqLights", "backYardLights", "poolLight", "spaLight"])], 
                  ["Shades", self.resources.getResList(["shade1", "shade2", "shade3", "shade4"])], 
                  ["Sprinklers", self.resources.getResList(["backLawn", "backBeds", "sideBeds"])]
                  ]
        reply = self.env.get_template("ipad.html").render(script=script, 
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
        if debugWeb: log("get", action, resource)
        if resource:
            self.resources[resource].setViewState(action)
            script = redirectScript("/iphone3gs", 5)
        else:
            script = updateScript(30)
        # lock.acquire()
        resources = self.resources.getResList(["frontLights", "backLights", "bedroomLight", "recircPump"])
        reply = self.env.get_template("iphone3gs.html").render(script=script, 
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
                            resources=self.resources.getResList(["gardenSequence", "backLawnSequence", "sideBedSequence", "backLawn", "backBeds", "sideBeds", "frontLawn"]), 
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
        # lock.acquire()
        for resource in self.resources:
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

class BeaconClient(threading.Thread):
    """ Beacon client thread.

    """
    def __init__(self, theName, resources, selfBeacon=""):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.doBeacon)
        self.name = theName
        self.servers = {}
        self.resources = resources
        self.selfBeacon = selfBeacon
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("", 4242))
                
    def doBeacon(self):
        """ Message handling loop.
        """
        if debugThread: log(self.name, "started")
        # wake up every second
        while running:
            # loop until the program state changes to not running
            (data, addr) = self.socket.recvfrom(4096)
            #log ("beacon data", data)
            server = json.loads(data)
            serverName = server[0]+":"+str(server[1])
            serverAddr = addr[0]+":"+str(server[1])
            serverResources = server[2]
            if serverName != self.selfBeacon:   # ignore the beacon from this service
                if serverAddr not in self.servers.values():
                    # lock.acquire()
                    resources.load(HARestInterface(serverName, serverAddr, secure=False), "/"+serverResources["name"])
                    resources.addViews(views)
                    # lock.release()
                    self.servers[serverName] = serverAddr
        if debugThread: log(self.name, "terminated")


if __name__ == "__main__":

    # load the resources from the HA servers
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
    beacon = BeaconClient("beaconClient", resources, socket.gethostname()+":"+str(beaconPort))
    beacon.start()
    
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
    access_log = cherrypy.log.access_log
    for handler in tuple(access_log.handlers):
        access_log.removeHandler(handler)
    cherrypy.engine.start()

    # start the REST server for this service
    restServer = RestServer(resources, beaconPort, secure=True)
    restServer.start()

