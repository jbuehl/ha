webPort = 80
webRestPort = 7478
webUpdateInterval = 1
webPageTitle = "Home Automation"
authCode = "01234567"

insideTemp = "kitchenTemp"
outsideTemp = "deckTemp"
poolTemp = "waterTemp"

import json
import cherrypy
from cherrypy.lib import auth_basic
from jinja2 import Environment, FileSystemLoader
from ha.HAClasses import *
from haWebViews import *

# user authentication
userFileName = keyDir+"users.json"
users = json.load(open(userFileName))
def validatePassword(realm, username, password):
    if username in users and users[username] == password:
       return True
    return False
        
class WebRoot(object):
    def __init__(self, resources, env, cache, stateChangeEvent, resourceLock):
        self.resources = resources
        self.env = env
        self.cache = cache
        self.stateChangeEvent = stateChangeEvent
        self.resourceLock = resourceLock
    
    # Everything    
    @cherrypy.expose
    def index(self, group=None):
        debug('debugWeb', "/", "get", group)
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

    # Tacoma    
    @cherrypy.expose
    def tacoma(self):
        debug('debugWeb', "/", "get")
        with self.resourceLock:
            reply = self.env.get_template("tacoma.html").render(title=webPageTitle, script="", 
                                group=self.resources.getGroup("Tacoma"),
                                views=views)
        return reply

    # Solar   
    @cherrypy.expose
    def solar(self, action=None, resource=None):
        debug('debugWeb', "/solar", "get", action, resource)
        with self.resourceLock:
            inverters = self.resources.getGroup("Inverters")
            optimizers = self.resources.getGroup("Optimizers")
            latitude = "%7.3f "%(abs(latLong[0])+.0005)+("N" if latLong[0]>0 else "S")
            longitude = "%7.3f "%(abs(latLong[1])+.0005)+("E" if latLong[1]>0 else "W")
            reply = self.env.get_template("solar.html").render(script="",
                                dayOfWeek=self.resources.getRes("theDayOfWeek"),
                                date=self.resources.getRes("theDate"),
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                sunrise=self.resources.getRes("sunrise"),
                                sunset=self.resources.getRes("sunset"),
                                latitude=latitude, longitude=longitude,
                                airTemp=self.resources.getRes(outsideTemp),
                                inverterTemp=self.resources.getRes("inverterTemp"), 
                                roofTemp=self.resources.getRes("roofTemp"), 
                                currentLoad=self.resources.getRes("currentLoad"), 
                                currentPower=self.resources.getRes("currentPower"), 
                                todaysEnergy=self.resources.getRes("todaysEnergy"), 
                                lifetimeEnergy=self.resources.getRes("lifetimeEnergy"), 
                                inverters=inverters, 
                                optimizers=optimizers, 
                                views=views)
        return reply

    # iPad - 1024x768   
    @cherrypy.expose
    def ipad(self, action=None, resource=None):
        debug('debugWeb', "/ipad", "get", action, resource)
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
    @cherrypy.expose
    def iphone5(self, action=None, resource=None):
        debug('debugWeb', "/iphone5", "get", action, resource)
        with self.resourceLock:
            reply = self.env.get_template("iphone5.html").render(script="", 
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                temp=self.resources.getRes(outsideTemp),
                                resources=self.resources.getResList(["spaTemp", "porchLights", "allShades", "shade1", "shade2", "shade3", "shade4", "backLawn", "backBeds", "garden", "sideBeds", "frontLawn"]),
                                views=views)
        return reply

    # iPhone 3GS - 320x480    
    @cherrypy.expose
    def iphone3gs(self, action=None, resource=None):
        debug('debugWeb', "/iphone3gs", "get", action, resource)
        with self.resourceLock:
            reply = self.env.get_template("iphone3gs.html").render(script="", 
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                day=self.resources.getRes("theDay"),
                                temp=self.resources.getRes(outsideTemp),
                                resources=self.resources.getResList(["porchLights", "xmasLights", "bedroomLights", "recircPump", "garageDoors", "houseDoors"]),
                                views=views)
        return reply

    # get or set a resource state
    @cherrypy.expose
    def cmd(self, resource=None, state=None):
        debug('debugWeb', "/cmd", "get", resource, state)
        try:
            if resource == "resources":
                reply = ""
                for resource in self.resources.keys():
                    if resource != "states":
                        reply += resource+"\n"
                return reply
            else:
                if state:
                    self.resources.getRes(resource).setViewState(state, views)
                    time.sleep(1)   # hack
                return json.dumps({"state": self.resources.getRes(resource).getViewState(views)})
        except:
            return "Error"        

    # Return the value of a resource attribute
    @cherrypy.expose
    def value(self, resource=None, attr=None):
        try:
            if resource:
                if attr:
                    return self.resources.getRes(resource).__getattribute__(attr).__str__()
                else:
                    return self.resources.getRes(resource).dict().__str__()
        except:
            return "Error"        

    # Update the states of all resources
    @cherrypy.expose
    def state(self, _=None):
        debug('debugWebUpdate', "state", cherrypy.request.remote.ip)
        return self.updateStates(self.resources.getRes("states").getState())
        
    # Update the states of resources that have changed
    @cherrypy.expose
    def stateChange(self, _=None):
        debug('debugWebUpdate', "stateChange", cherrypy.request.remote.ip)
        debug('debugInterrupt', "update", "event wait")
        self.stateChangeEvent.wait()
        debug('debugInterrupt', "update", "event clear")
        self.stateChangeEvent.clear()
        return self.updateStates(self.resources.getRes("states").getStateChange())

    # return the json to update the states of the specified collection of sensors
    def updateStates(self, resourceStates):
        staticTypes = ["time", "ampm", "date", "W", "KW"]          # types whose class does not depend on their value
        tempTypes = ["tempF", "tempFControl", "tempC", "spaTemp"]       # temperatures
        if self.cache:
            cacheTime = self.cache.cacheTime
        else:
            cacheTime = 0
        updates = {"cacheTime": cacheTime}
        for resource in resourceStates.keys():
            try:
                resState = self.resources.getRes(resource).getViewState(views)
                resClass = self.resources.getRes(resource).type
                if resClass in tempTypes:
                    updates[resource] = ("temp", resState, tempColor(resState))
                else:
                    if resClass not in staticTypes:
                        resClass += "_"+resState
                    updates[resource] = (resClass, resState, "")
            except:
                pass
        debug('debugWebUpdate', "states", len(updates))
        return json.dumps(updates)
        
    # Submit    
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        debug('debugWeb', "/submit", "post", action, resource)
        self.resources.getRes(resource).setViewState(action, views)
        reply = ""
        return reply

def webInit(resources, restCache, stateChangeEvent, resourceLock, httpPort=80, ssl=False, httpsPort=443, domain=""):
    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
    appConfig = {
        '/': {
           'tools.auth_basic.on': True,
           'tools.auth_basic.realm': 'localhost',
           'tools.auth_basic.checkpassword': validatePassword
        },
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
        '/images': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': os.path.join(baseDir, "static"),
            'tools.staticdir.dir': "images",
        },
        '/favicon.ico': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(baseDir, "static/favicon.ico"),
        },
    }    
    root = WebRoot(resources, Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates'))), restCache, stateChangeEvent, resourceLock)
    cherrypy.tree.mount(root, "/", appConfig)
    
    cherrypy.server.unsubscribe()
    # http server for LAN access
    httpServer = cherrypy._cpserver.Server()
    httpServer.socket_port = httpPort
    httpServer._socket_host = "0.0.0.0"
    httpServer.max_request_body_size = 120 * 1024 # ~100kb
    httpServer.thread_pool = 30
    httpServer.subscribe()
    if ssl:
        # https server for external access
        httpsServer = cherrypy._cpserver.Server()
        httpsServer.socket_port = httpsPort
        httpsServer._socket_host = '0.0.0.0'
        httpsServer.max_request_body_size = 120 * 1024 # ~100kb
        httpsServer.thread_pool = 30
        httpsServer.ssl_module = 'pyopenssl'
        httpsServer.ssl_certificate = keyDir+domain+".crt"
        httpsServer.ssl_private_key = keyDir+domain+".key"
        httpsServer.subscribe()

    if not webLogging:
        access_log = cherrypy.log.access_log
        for handler in tuple(access_log.handlers):
            access_log.removeHandler(handler)
    cherrypy.engine.timeout_monitor.unsubscribe()
    cherrypy.engine.autoreload.unsubscribe()
    cherrypy.engine.start()
        
