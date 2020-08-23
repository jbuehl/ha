webLogging = False
webReload = False
debugWebUpdateTime = False
debugWebStateTime = False
debugWebStateChangeTime = False
blinkers = []

import json
import subprocess
import cherrypy
import time
from cherrypy.lib import auth_basic
import requests
import urllib.request, urllib.parse, urllib.error
from twilio.rest import Client
from ha import *
from ha.ui.webViews import *
from ha.notification.notificationServer import *
from ha.camera.events import *
from ha.camera.video import *

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

voiceCommands = {
                "bedroom cooling": "northCoolTempTarget",
                "bedroom ac": "northCoolTempTarget",
                "bedroom heat": "northHeatTempTarget",
                "family room cooling": "southCoolTempTarget",
                "family room ac": "southCoolTempTarget",
                "family room heat": "southHeatTempTarget",
                "back house cooling": "backCoolTempTarget",
                "back house ac": "backCoolTempTarget",
                "back house heat": "backHeatTempTarget",
                "spa temperature": "spaTempTarget",
                "hot tub temperature": "spaTempTarget",
                }

def translateVoice(phrase):
    try:
        return voiceCommands[phrase.lower().lstrip("the ")]
    except KeyError:
        return phrase

class WebRoot(object):
    def __init__(self, resources, cache, stateChangeEvent, pathDict):
        self.resources = resources
        # self.resourceStateSensor = self.resources.getRes("states")
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
        resourceTypes = {}  # cache for resource types
        while True:
            debug('debugWebState', "updateStates", "event clear")
            self.updateStateChangeEvent.clear()
            # wait for sensor states to change
            resourceStates = self.resources.getStates(wait=True)
            if self.cache:
                cacheTime = self.cache.cacheTime
            else:
                cacheTime = 0
            updates = {"cacheTime": cacheTime}
            blinkerList = []
            for resourceName in list(resourceStates.keys()):
                try:
                    state = resourceStates[resourceName]
                    if state != None:   # ignore null states
                        try:
                            resType = resourceTypes[resourceName]
                        except KeyError:
                            resType = self.resources.getRes(resourceName).type
                            resourceTypes[resourceName] = resType
                        resState = views.getViewState(None, resType, state)
                        jqueryName = resourceName.replace(".", "_") # jquery doesn't like periods in names
                        debug('debugWebUpdate', "/updateStates", resourceName, resType, resState, state)
                        # determine the HTML class for the resource
                        if resType in tempTypes:         # temperature
                            updates[jqueryName] = ("temp", resState)
                        elif (resourceName[0:16] == "solar.optimizers") and (resourceName[-5:] == "power"):
                            updates[jqueryName] = ("panel", resState)
                        elif resType in staticTypes:
                            if resType[-1] == "-":      # + or - value
                                updates[jqueryName] = (resType[:-1]+("_plus" if state >= 0 else "_minus"), resState)
                            else:                       # class doesn't depend on value
                                updates[jqueryName] = (resType, resState)
                        else:                           # class is specific to the type and value
                            updates[jqueryName] = (resType+"_"+resState, resState)
                        if (resourceName in blinkers) and state:
                            debug('debugWebBlink', "/updateStates", resourceName, resType, resState, state)
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
            return bytes(path+" not found", "utf-8")

    # get or set a resource state
    @cherrypy.expose
    def cmd(self, resource=None, state=None):
        debug('debugWeb', "/cmd", cherrypy.request.method, resource, state)
        try:
            if resource == "resources":
                reply = ""
                for resource in list(self.resources.keys()):
                    if resource != "states":
                        reply += resource+"\n"
                return reply
            else:
                if state:
                    views.setViewState(self.resources.getRes(translateVoice(resource)), state.strip().capitalize())
                    time.sleep(1)   # hack
                return json.dumps({"state": views.getViewState(self.resources.getRes(resource))})
        except:
            return bytes("Error", "utf-8")

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
        return bytes(response, "utf-8")

    # Update the states of all resources
    @cherrypy.expose
    def state(self, _=None):
        ts = time.time()
        debug('debugWeb', "/state", "start", ts)
        debug('debugWebState', "state", "lock")
        with self.updateLock:
            stateJson = self.stateJson
            debug('debugWebState', "state", "unlock")
        cherrypy.response.headers['Content-Type'] = "application/json"
        cherrypy.response.headers['Content-Length'] = len(stateJson)
        debug('debugWeb', "/state", "end", ts)
        return bytes(stateJson, "utf-8")

    # Update the states of resources when there is a change
    @cherrypy.expose
    def stateChange(self, _=None):
        ts = time.time()
        debug('debugWeb', "/stateChange", "start", ts)
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
        cherrypy.response.headers['Content-Length'] = len(stateJson)
        debug('debugWeb', "/stateChange", "end", ts)
        return bytes(stateJson, "utf-8")

    # change the state of a control
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        debug('debugWeb', "/submit", cherrypy.request.method, action, resource)
        views.setViewState(self.resources.getRes(resource), action)
        reply = ""
        return bytes(reply, "utf-8")

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
    def notify(self, eventType, message):
        if eventType == "alertDoorbell":
            eventTime = time.strftime("%Y%m%d%H%M%S")
            camera = "frontdoor"
            message += " https://shadyglade.thebuehls.com/"
            message += "image/"+camera+"/"+eventTime[0:8]+"/"
            message += eventTime+"_doorbell"
            createEvent("doorbell", camera, eventTime)
        notify(self.resources, eventType, message)

    # return a camera image
    def getImage(self, camera, date, image, imageType):
        if not camera:
            cherrypy.response.status = 400
            return "camera is required"
        if not date:
            date = time.strftime("%Y%m%d")
        imageDir = cameraDir+camera+"/"+imageType+"/"+dateDir(date)
        if image:
            image = image.split(".")[0]+".jpg"
        else:
            # use the latest image in the directory
            imageFiles = os.listdir(imageDir)
            for imageFile in sorted(imageFiles, reverse=True):
                if imageFile.split(".")[-1] == "jpg":
                    image = imageFile
                    break
            if not image:
                cherrypy.response.status = 404
                return "no images available"
        debug('debugImage', "camera = ", camera)
        debug('debugImage', "date = ", date)
        debug('debugImage', "imageType = ", imageType)
        debug('debugImage', "image = ", image)
        with open(imageDir+image, "rb") as imageFile:
            imageContent = imageFile.read()
        debug('debugImage', "length = ", len(imageContent))
        cherrypy.response.headers['Content-Type'] = "image/jpeg"
        cherrypy.response.headers['Content-Length'] = len(imageContent)
        return imageContent

    # return a camera image
    @cherrypy.expose
    def image(self, camera=None, date=None, image=None):
        return self.getImage(camera, date, image, "images")

    # return a camera thumbnail
    @cherrypy.expose
    def thumb(self, camera=None, date=None, thumb=None):
        return self.getImage(camera, date, thumb, "thumbs")

    # return a camera snapshot
    @cherrypy.expose
    def snap(self, camera=None, date=None, snap=None):
        return self.getImage(camera, date, snap, "snaps")

    # return a video resource for a camera
    @cherrypy.expose
    def video(self, camera=None, date=None, resource=None):
        if not camera:
            cherrypy.response.status = 400
            return "camera is required"
        if not date:
            date = time.strftime("%Y%m%d")
        videoDir = cameraDir+camera+"/videos/"+dateDir(date)
        if resource:
            (resourceName, resourceType) = resource.split(".")
        else:
            # return newest playlist
            videos = os.listdir(videoDir)
            for video in sorted(videos, reverse=True):
                if video.split(".")[-1] == "m3u8":
                    resource = video
                    resourceType = "m3u8"
                    break
        debug('debugResource', "camera = ", camera)
        debug('debugResource', "date = ", date)
        debug('debugResource', "resource = ", resource)
        try:
            (start, end) = urllib.parse.unquote(resourceName).split(":")
            # create a playlist on the fly
            start = "%06d"%int(start)
            if end == "":
                # default is 1 minute
                end = "%06d"%(int(start)+59)
            debug('debugResource', "playlist = ", start, end)
            (chunkList, eventList) = getPlaylists(videoDir)
            resourceContent = bytes(makePlaylist(date+start, date+end, chunkList), "utf-8")
        except ValueError:
            with open(videoDir+resource, "rb") as resourceFile:
                resourceContent = resourceFile.read()
        debug('debugResource', "length = ", len(resourceContent))
        cherrypy.response.headers['Content-Length'] = len(resourceContent)
        if resourceType == "m3u8":
            cherrypy.response.headers['Content-Type'] = "application/x-mpegURL"
        elif resourceType == "ts":
            cherrypy.response.headers['Content-Type'] = "video/mp2t"
        elif resourceType == "mp4":
            cherrypy.response.headers['Content-Type'] = "video/mp4"
        else:
            cherrypy.response.headers['Content-Type'] = "application/octet-stream"
        return resourceContent

    # return a video clip for a camera
    @cherrypy.expose
    def clip(self, camera=None, date=None, starthour=None, startminute=None, endhour=None, endminute=None, archive=None):
        if not camera:
            cherrypy.response.status = 400
            return "camera is required"
        if not date:
            date = time.strftime("%Y%m%d")
        videoDir = cameraDir+camera+"/videos/"+dateDir(date)
        duration = (int(endhour) * 3600 + int(endminute) * 60) - (int(starthour) * 3600 + int(startminute) * 60)
        clipFileName = makeClip(videoDir, date+starthour+startminute, duration, "mp4")
        videoClip = open(videoDir+clipFileName, "rb").read()
        # archive the clip or delete it
        if archive == "true":
            debug('debugClip', "archiving", clipFileName)
            archiveDir = cameraBase+"archive/"+camera+"/videos/"+dateDir(date)
            makeDir(archiveDir)
            os.rename(videoDir+clipFileName, archiveDir+clipFileName)
        else:
            debug('debugClip', "deleting", clipFileName)
            os.remove(videoDir+clipFileName)
        cherrypy.response.headers['Content-Length'] = len(videoClip)
        cherrypy.response.headers['Content-Type'] = "application/octet-stream"
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="'+camera+'-'+clipFileName+'"'
        return videoClip

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
