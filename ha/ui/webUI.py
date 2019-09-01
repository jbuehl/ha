webLogging = False
webReload = False
debugWebUpdateTime = False
debugWebStateTime = False
debugWebStateChangeTime = False
blinkers = []
imageBase = "/var/ftp/images/"

import json
import subprocess
import cherrypy
import time
from cherrypy.lib import auth_basic
import requests
from twilio.rest import Client
from ha import *
from ha.ui.webViews import *
from ha.notification.notificationServer import *

twilioKey = keyDir+"twilio.key"

# https://cherrypy.readthedocs.io/en/3.2.6/progguide/extending/customtools.html
# https://bitbucket.org/cherrypy/cherrypy/src/ea210e8ef58a3a6ca289a8564c389e38de13d3d5/cherrypy/lib/auth_basic.py?at=default&fileviewer=file-view-default

# user authentication
userFileName = keyDir+"users.json"
users = []
lanAddr = "192.168.1"
def validatePassword(realm, username, password):
    global users
    debug('debugWebAuth', "validatePassword", "ip:", cherrypy.request.remote.ip, "username:", username, "password:", password)
    if users == []:
        debug('debugWebAuth', "validatePassword", "reading user file", userFileName)
        users = json.load(open(userFileName))
    # accept anything connecting from the LAN
    if ".".join(cherrypy.request.remote.ip.split(".")[0:3]) == lanAddr:
        debug('debugWebAuth', "validatePassword", "accepted")
        return True
    # validate the credentials
    if username in users and users[username] == password:
        debug('debugWebAuth', "validatePassword", "accepted")
        return True
    debug('debugWebAuth', "validatePassword", "rejected")
    return False

class WebRoot(object):
    def __init__(self, resources, cache, stateChangeEvent, pathDict):
        self.resources = resources
        self.resourceStateSensor = self.resources.getRes("states")
        self.cache = cache
        self.resourceStateChangeEvent = stateChangeEvent
        self.updateStateChangeEvent = threading.Event()
        self.updateLock = threading.Lock()
        self.stateJson = ""     # current state and type of all sensors in json format
        updateStatesThread = threading.Thread(target=self.updateStates)
        updateStatesThread.start()
        self.pathDict = pathDict

    # thread to update the states of the sensors in the resource collection
    def updateStates(self):
        while True:
            debug('debugWebState', "updateStates", "event clear")
            self.updateStateChangeEvent.clear()
            # wait for sensor states to change
            resourceStateTypes = self.resourceStateSensor.getStateChangeTypes()
            if self.cache:
                cacheTime = self.cache.cacheTime
            else:
                cacheTime = 0
            updates = {"cacheTime": cacheTime}
            blinkerList = []
            for resource in resourceStateTypes.keys():
                try:
                    state = resourceStateTypes[resource][0] # self.resources.getRes(resource).getState()
                    resClass = resourceStateTypes[resource][1] # self.resources.getRes(resource).type
                    resState = views.getViewState(None, resClass, state) # views.getViewState(self.resources.getRes(resource))
                    jqueryName = resource.replace(".", "_") # jquery doesn't like periods in names
                    debug('debugWebUpdate', "/updateStates", resource, resClass, resState, state)
                    if resClass in tempTypes:
                        updates[jqueryName] = ("temp", resState)
                    elif (resource[0:16] == "solar.optimizers") and (resource[-5:] == "power"):
                        updates[jqueryName] = ("panel", resState)
                    else:
                        if resClass not in staticTypes:
                            resClass += "_"+resState
                        updates[jqueryName] = (resClass, resState)
                    if (resource in blinkers) and (state > 0):
                        debug('debugWebBlink', "/updateStates", resource, resClass, resState, state)
                        blinkerList.append(jqueryName)
                except:
                    raise
            debug('debugWebBlink', "/updateStates", blinkerList)
            updates["blinkers"] = blinkerList
            debug('debugWebState', "updateStates", "lock")
            with self.updateLock:
                self.stateJson = json.dumps(updates)
                debug('debugWebState', "updateStates", "unlock")
            debug('debugWebState', "updateStates", "event set")
            self.updateStateChangeEvent.set()

    # convert the path into a request parameter
    # this function gets called if cherrypy doesn't find a class method that matches the path
    def _cp_dispatch(self, vpath):
        debug('debugWeb', "_cp_dispatch", "method:", cherrypy.request.method, "path:", vpath.__str__(), "params:", cherrypy.request.params.__str__())
        if len(vpath) == 1:
            # the path has one element, pop it off and return this root object
            # cherrypy will then call the index()
            cherrypy.request.params['path'] = vpath.pop(0)
            return self
        # the request was for a file in the static/ directory, return the path
        return vpath

    # dispatch to the UI requested
    @cherrypy.expose
    def index(self, path="", **params):
        debug('debugWeb', "index", cherrypy.request.method, "path:", path, "params:", params.__str__())
        try:
            return self.pathDict[path](**params)
        except KeyError:
            cherrypy.response.status = 404
            return path+" not found"

    # get or set a resource state
    @cherrypy.expose
    def cmd(self, resource=None, state=None):
        debug('debugWeb', "/cmd", cherrypy.request.method, resource, state)
        try:
            if resource == "resources":
                reply = ""
                for resource in self.resources.keys():
                    if resource != "states":
                        reply += resource+"\n"
                return reply
            else:
                if state:
                    views.setViewState(self.resources.getRes(resource), state.strip().capitalize())
                    time.sleep(1)   # hack
                return json.dumps({"state": views.getViewState(self.resources.getRes(resource))})
        except:
            return "Error"

    # Return the value of a resource attribute
    @cherrypy.expose
    def value(self, resource=None, attr=""):
        debug('debugWeb', "/value", cherrypy.request.method, resource, attr)
        try:
            if resource:
                if attr != "":
                    response = json.dumps({attr: self.resources[resource].dict()[attr]})
                else:
                    response = json.dumps(self.resources[resource].dict())
                cherrypy.response.headers['Content-Type'] = "application/json"
            else:
                cherrypy.response.status = 400
                response = "Resource not specified"
        except KeyError:
            cherrypy.response.status = 404
            response = resource+"/"+attr+" not found"
        except:
            cherrypy.response.status = 500
            response = "Error"
        return response

    # Update the states of all resources
    @cherrypy.expose
    def state(self, _=None):
        debug('debugWebUpdate', "/state", cherrypy.request.method)
        debug('debugWebState', "state", "lock")
        with self.updateLock:
            stateJson = self.stateJson
            debug('debugWebState', "state", "unlock")
        cherrypy.response.headers['Content-Type'] = "application/json"
        return stateJson

    # Update the states of resources when there is a change
    @cherrypy.expose
    def stateChange(self, _=None):
        debug('debugWebUpdate', "/stateChange", cherrypy.request.method)
        # wait for the states to update
        debug('debugWebState', "stateChange", "event wait")
        self.updateStateChangeEvent.wait()
        debug('debugWebState', "stateChange", "event clear")
        self.updateStateChangeEvent.clear()
        debug('debugWebState', "stateChange", "lock")
        with self.updateLock:
            stateJson = self.stateJson
            debug('debugWebState', "stateChange", "unlock")
        cherrypy.response.headers['Content-Type'] = "application/json"
        return stateJson

    # change the state of a control
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        debug('debugWeb', "/submit", cherrypy.request.method, action, resource)
        views.setViewState(self.resources.getRes(resource), action)
        reply = ""
        return reply

    # return a camera image
    @cherrypy.expose
    def image(self, camera=None, date=None, image=None):
        debug('debugWeb', "/image", cherrypy.request.method, camera)
        if not camera:
            camera = "frontdoor"
        if not image:
            image = subprocess.check_output("ls -1 /var/ftp/images/"+camera+"/*.jpg | tail -n1", shell=True).split("/")[-1].strip("\n")
        if not date:
            date = time.strftime("%Y%m%d")
        year = date[0:4]
        month = date[4:6]
        day = date[6:8]
        debug('debugImage', "camera = ", camera)
        debug('debugImage', "date = ", date)
        debug('debugImage', "image = ", image)
        imageDir = imageBase+camera+"/"+year+"/"+month+"/"+day+"/"
        with open(imageDir+image) as imageFile:
            imageContent = imageFile.read()
        debug('debugImage', "length = ", len(imageContent))
        cherrypy.response.headers['Content-Type'] = "image/jpeg"
        cherrypy.response.headers['Content-Length'] = len(imageContent)
        return imageContent

    # return a camera video
    @cherrypy.expose
    def video(self, camera=None, date=None, video=None):
        debug('debugWeb', "/video", cherrypy.request.method, camera)
        if not camera:
            camera = "frontdoor"
        if not video:
            video = subprocess.check_output("ls -1 /var/ftp/images/"+camera+"/*.mp4 | tail -n1", shell=True).split("/")[-1].strip("\n")
        if not date:
            date = time.strftime("%Y%m%d")
        year = date[0:4]
        month = date[4:6]
        day = date[6:8]
        debug('debugImage', "camera = ", camera)
        debug('debugImage', "date = ", date)
        debug('debugImage', "video = ", video)
        imageDir = imageBase+camera+"/"+year+"/"+month+"/"+day+"/"
        with open(imageDir+video) as videoFile:
            videoContent = videoFile.read()
        debug('debugImage', "length = ", len(video))
        cherrypy.response.headers['Content-Type'] = "video/mp4"
        cherrypy.response.headers['Content-Length'] = len(videoContent)
        return videoContent

    # return a sound
    @cherrypy.expose
    def sound(self, sound=None):
        debug('debugWeb', "/sound", cherrypy.request.method, sound)
        debug('debugSound', "sound = ", sound)
        with open(soundDir+sound) as soundFile:
            soundContent = soundFile.read()
        debug('debugSound', "length = ", len(soundContent))
        cherrypy.response.headers['Content-Type'] = "audio/wav"
        cherrypy.response.headers['Content-Length'] = len(soundContent)
        return soundContent

    # send a notification
    @cherrypy.expose
    def notify(self, type, message):
        notify(self.resources, type, message)

def webInit(resources, restCache, stateChangeEvent, httpPort=80, ssl=False, httpsPort=443, domain="", pathDict=None, baseDir="/", block=False):
    # set up the web server
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
    if ssl:
        appConfig.update({
            '/': {
               'tools.auth_basic.on': True,
               'tools.auth_basic.realm': 'localhost',
               'tools.auth_basic.checkpassword': validatePassword
            }})

    # create a resource state sensor if there isn't one
    try:
        stateResource = self.resources.getRes("states", dummy=False)
    except:
        debug('debugWeb', "created resource state sensor")
        stateResource = ResourceStateSensor("states", Interface("None"), resources=resources, event=stateChangeEvent)
        resources.addRes(stateResource)

    root = WebRoot(resources, restCache, stateChangeEvent, pathDict)
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
    if not webReload:
        # cherrypy.engine.timeout_monitor.unsubscribe()
        cherrypy.engine.autoreload.unsubscribe()
    cherrypy.engine.start()
    if block:
        cherrypy.engine.block()
