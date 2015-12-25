webPort = 80
webRestPort = 7478
webUpdateInterval = 1
webPageTitle = "Home Automation"

insideTemp = "kitchenTemp"
outsideTemp = "deckTemp"
poolTemp = "waterTemp"

import cherrypy
import json
from jinja2 import Environment, FileSystemLoader
from ha.HAClasses import *
from haWebViews import *

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
            groups = ["Time", "Temperature", "Hvac", "Services", "Pool", "Lights", "Doors", "Water", "Solar", "Power", "Cameras", "Tasks"]
            details = True
        with self.resourceLock:
            reply = self.env.get_template("default.html").render(title=webPageTitle, script="", 
                                groups=[[group, self.resources.getGroup(group)] for group in groups],
                                views=views,
                                details=details)
        return reply

    # iPad - 1024x768   
    @cherrypy.expose
    def ipad(self, action=None, resource=None):
        debug('debugWeb', "/ipad", "get", action, resource)
        with self.resourceLock:
            reply = self.env.get_template("ipad.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                day=self.resources["theDay"],
                                pooltemp=self.resources[poolTemp],
                                intemp=self.resources[insideTemp],
                                outtemp=self.resources[outsideTemp],
                                groups=[["Pool", self.resources.getResList(["spaTemp"])], 
                                      ["Lights", self.resources.getResList(["xmasTree", "xmasCowTree", "porchLights", "xmasLights", "bbqLights", "backYardLights", "poolLight", "spaLight"])], 
                                      ["Shades", self.resources.getResList(["allShades", "shade1", "shade2", "shade3", "shade4"])], 
                                      ["Hvac", self.resources.getResList(["southHeatTempTarget", "northHeatTempTarget1"])], 
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
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                temp=self.resources[outsideTemp],
                                resources=self.resources.getResList(["spaTemp", "xmasTree", "xmasCowTree", "porchLights", "xmasLights", "allShades", "shade1", "shade2", "shade3", "shade4", "backLawn", "backBeds", "garden", "sideBeds", "frontLawn"]),
                                views=views)
        return reply

    # iPhone 3GS - 320x480    
    @cherrypy.expose
    def iphone3gs(self, action=None, resource=None):
        debug('debugWeb', "/iphone3gs", "get", action, resource)
        with self.resourceLock:
            reply = self.env.get_template("iphone3gs.html").render(script="", 
                                time=self.resources["theTime"],
                                ampm=self.resources["theAmPm"],
                                day=self.resources["theDay"],
                                temp=self.resources[outsideTemp],
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
                    self.resources[resource].setViewState(state, views)
                    time.sleep(1)   # hack
                return json.dumps({"state": self.resources[resource].getViewState(views)})
        except:
            return "Error"        

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
        debug('debugWebUpdate', "state", cherrypy.request.remote.ip)
        return self.updateStates(self.resources["states"].getState())
        
    # Update the states of resources that have changed
    @cherrypy.expose
    def stateChange(self, _=None):
        debug('debugWebUpdate', "stateChange", cherrypy.request.remote.ip)
        debug('debugInterrupt', "update", "event wait")
        self.stateChangeEvent.wait()
        debug('debugInterrupt', "update", "event clear")
        self.stateChangeEvent.clear()
        return self.updateStates(self.resources["states"].getStateChange())

    # return the json to update the states of the specified collection of sensors
    def updateStates(self, resourceStates):
        staticTypes = ["time", "ampm", "date"]          # types whose class does not depend on their value
        tempTypes = ["tempF", "tempFControl", "tempC", "spaTemp"]       # temperatures
        updates = {"cacheTime": self.cache.cacheTime}
        for resource in resourceStates.keys():
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
        debug('debugWebUpdate', "states", len(updates))
        return json.dumps(updates)
        
    # Submit    
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        debug('debugWeb', "/submit", "post", action, resource)
        self.resources[resource].setViewState(action, views)
        reply = ""
        return reply

def webInit(resources, restCache, stateChangeEvent, resourceLock):
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
    root = WebRoot(resources, Environment(loader=FileSystemLoader(os.path.join(baseDir, 'templates'))), restCache, stateChangeEvent, resourceLock)
    cherrypy.tree.mount(root, "/", appConfig)
    if not webLogging:
        access_log = cherrypy.log.access_log
        for handler in tuple(access_log.handlers):
            access_log.removeHandler(handler)
    cherrypy.engine.timeout_monitor.unsubscribe()
    cherrypy.engine.autoreload.unsubscribe()
    cherrypy.engine.start()

