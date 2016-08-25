import threading
import time
import cherrypy
from jinja2 import Environment, FileSystemLoader

from ha.HAClasses import *
from ha.fileInterface import *
from ha.timeInterface import *
from ha.I2CInterface import *
from ha.TC74Interface import *
from ha.tempInterface import *
from ha.imuInterface import *
from ha.audioInterface import *
from ha.restServer import *
from ha.haWebViews import *

rootDir = "/root/"
dataDir = rootDir+"data/"
audioDir = "audio/"
gpsFileName = dataDir+"gps.json"
diagFileName = dataDir+"diags.json"
imuFileName = dataDir+"9dof.json"
audioFileName = audioDir+"audio.json"

class WebRoot(object):
    def __init__(self, resources, env, cache, stateChangeEvent, resourceLock):
        self.resources = resources
        self.env = env
        self.cache = cache
        self.stateChangeEvent = stateChangeEvent
        self.resourceLock = resourceLock
    
    # Tacoma - 800x480
    @cherrypy.expose
    def tacoma(self):
        debug('debugWeb', "/tacoma", cherrypy.request.method)
        with self.resourceLock:
            reply = self.env.get_template("tacoma.html").render(title=webPageTitle, script="", 
                                time=self.resources.getRes("theTime"),
                                ampm=self.resources.getRes("theAmPm"),
                                day=self.resources.getRes("theDay"),
                                temp=self.resources.getRes("outsideTemp"),
                                controls=[self.resources.getRes("volume"),
                                          self.resources.getRes("mute"),
                                          self.resources.getRes("wifi"),
                                         ],
                                group=self.resources.getGroup("Tacoma"),
                                views=views)
        return reply

    # Update the states of all resources
    @cherrypy.expose
    def state(self, _=None):
        debug('debugWebUpdate', "/state", cherrypy.request.method)
        return self.updateStates(self.resources.getRes("states").getState())
        
    # Update the states of resources that have changed
    @cherrypy.expose
    def stateChange(self, _=None):
        debug('debugWebUpdate', "/stateChange", cherrypy.request.method)
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
        return json.dumps(updates)
        
    # Submit    
    @cherrypy.expose
    def submit(self, action=None, resource=None):
        debug('debugWeb', "/submit", cherrypy.request.method, action, resource)
        self.resources.getRes(resource).setViewState(action, views)
        reply = ""
        return reply

def webInit(resources, restCache, stateChangeEvent, resourceLock, httpPort=80, ssl=False, httpsPort=443, domain=""):
    # set up the web server
    baseDir = os.path.abspath(os.path.dirname(__file__))
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
    if not webReload:
        cherrypy.engine.timeout_monitor.unsubscribe()
        cherrypy.engine.autoreload.unsubscribe()
    cherrypy.engine.start()

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")
    resourceLock = threading.Lock()

    # Interfaces
    stateChangeEvent = threading.Event()
    timeInterface = TimeInterface("Time")
    gpsInterface = FileInterface("GPS", fileName=gpsFileName, readOnly=True, event=stateChangeEvent)
    diagInterface = FileInterface("Diag", fileName=diagFileName, readOnly=True, event=stateChangeEvent)
    ndofInterface = FileInterface("9dof", fileName=imuFileName, readOnly=True, event=stateChangeEvent)
    imuInterface = ImuInterface("IMU", ndofInterface)
    i2cInterface = I2CInterface("I2C", bus=1, event=stateChangeEvent)
    tc74Interface = TC74Interface("TC74", i2cInterface)
    tempInterface = TempInterface("Temp", tc74Interface, sample=1)
    audioInterface = AudioInterface("Audio", event=stateChangeEvent)

    # Sensors
    resources.addRes(HASensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(HASensor("theDate", timeInterface, "%B %d %Y", type="date", group="Time", label="Date"))
    resources.addRes(HASensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(HASensor("sunrise", timeInterface, "sunrise", type="time", group="Time", label="Sunrise"))
    resources.addRes(HASensor("sunset", timeInterface, "sunset", type="time", group="Time", label="Sunset"))
    resources.addRes(HASensor("theDay", timeInterface, "%a %b %d %Y", type="date", label="Day"))
    resources.addRes(HASensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(HASensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))
#    resources.addRes(HASensor("tacomaDate", timeInterface, "%B %d %Y", group="Tacoma", label="Date", type="date"))
#    resources.addRes(HASensor("tacomaTimeAmPm", timeInterface, "%I:%M %p", group="Tacoma", label="Time", type="time"))
#    resources.addRes(HASensor("gpsTime", gpsInterface, "Time", group="Tacoma", label="GPS time"))
    resources.addRes(HASensor("position", gpsInterface, "Pos", group="Tacoma", label="Position"))
    resources.addRes(HASensor("altitude", gpsInterface, "Alt", group="Tacoma", label="Elevation", type="Ft"))
    resources.addRes(HASensor("heading", gpsInterface, "Hdg", group="Tacoma", label="Heading", type="Deg"))
#    resources.addRes(HASensor("gpsSpeed", gpsInterface, "Speed", group="Tacoma", label="GPS speed", type="MPH"))
#    resources.addRes(HASensor("speed", diagInterface, "Speed", group="Tacoma", label="Speed", type="MPH"))
    resources.addRes(HASensor("rpm", diagInterface, "Rpm", group="Tacoma", label="RPM", type="RPM"))
    resources.addRes(HASensor("battery", diagInterface, "Battery", group="Tacoma", label="Battery", type="V"))
#    resources.addRes(HASensor("intakeTemp", diagInterface, "IntakeTemp", group="Tacoma", label="Intake air temp", type="tempC"))
    resources.addRes(HASensor("coolantTemp", diagInterface, "WaterTemp", group="Tacoma", label="Water temp", type="tempC"))
    resources.addRes(HASensor("airPressure", diagInterface, "Barometer", group="Tacoma", label="Barometer", type="barometer"))
    resources.addRes(HASensor("outsideTemp", tempInterface, 0x4e, group="Temp", label="Outside temp", type="tempF"))

    # Controls
    resources.addRes(HAControl("volume", audioInterface, "volume", group="Audio", label="Vol", type="audioVolume"))
    resources.addRes(HAControl("mute", audioInterface, "mute", group="Audio", label="Mute", type="audioMute"))
    resources.addRes(HAControl("wifi", audioInterface, "wifi", group="Audio", label="Wifi", type="wifi"))
    
    # Start interfaces
    gpsInterface.start()
    diagInterface.start()
    ndofInterface.start()
    tempInterface.start()

    # set up the web server
    webInit(resources, None, stateChangeEvent, resourceLock, httpPort=8080)

    # start the REST server for this service
    restServer = RestServer(resources, event=stateChangeEvent, label="Tacoma")
    # restServer.start()
    while True:
        time.sleep(1)
    
