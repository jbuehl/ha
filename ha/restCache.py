
from ha.HAClasses import *
from ha.restInterface import *
import json
import threading
import socket

# Cache of resource states for one or more REST servers

# Autodiscover servers and resources
# Detect changes in resources on each server
# Remove resources on servers that don't respond

class RestCache(threading.Thread):
    def __init__(self, name, resources, selfRest="", stateChangeEvent=None,  lock=None):
        debug('debugRestCache', name, "starting", selfRest)
        threading.Thread.__init__(self, target=self.doRest)
        self.name = name
        self.servers = {}
        self.resources = resources
        self.lock = lock
        self.stateChangeEvent = stateChangeEvent
        self.selfRest = selfRest
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("", 4242))
                
    def doRest(self):
        debug('debugThread', self.name, "started")
        while running:
            # loop until the program state changes to not running
            (data, addr) = self.socket.recvfrom(4096)
            debug('debugRestBeacon', self.name, "beacon data", data)
            server = json.loads(data)
            serverName = server[0]+":"+str(server[1])   # hostname:port
            serverAddr = addr[0]+":"+str(server[1])     # IPAddr:port
            serverResources = server[2]
            try:
                serverTimeStamp = server[3]
            except:
                serverTimeStamp = 0
            if serverName != self.selfRest:   # ignore the beacon from this service
                if serverName not in self.servers.keys():   # new server
                    debug('debugRestCache', self.name, "Adding", serverName, serverAddr, serverTimeStamp)
                    self.servers[serverName] = RestCacheServer(serverName, serverAddr, serverTimeStamp)
                    self.getResources(self.servers[serverName], serverResources, serverTimeStamp)
                else:
                    if serverTimeStamp > self.servers[serverName].timeStamp: # server resources changed
                        debug('debugRestCache', self.name, "Updating", serverName, serverAddr, serverTimeStamp)
                        self.delResources(self.servers[serverName])
                        self.getResources(self.servers[serverName], serverResources, serverTimeStamp)
                        
        debug('debugThread', self.name, "terminated")

    def getResources(self, server, serverResources, timeStamp):
        restInterface = HARestInterface(server.name, server=server.addr, event=self.stateChangeEvent, secure=False)
        resources = HACollection(server.name+" resources")
        resources.load(restInterface, "/"+serverResources["name"])
        server.resourceNames = resources.keys()
        server.timeStamp = timeStamp
        restInterface.readStates()          # fill the cache for these resources
        with self.lock:
            self.resources.update(resources)
            del(resources)

    def delResources(self, server):
        with self.lock:
            for resourceName in server.resourceNames:
                self.resources.delRes(resourceName)

# REST server that is being cached
class RestCacheServer(object):
    def __init__(self, name, addr, timeStamp=0, resourceNames=[]):
        debug('debugRestCache', name, "created")
        self.name = name
        self.addr = addr
        self.timeStamp = timeStamp
        self.resourceNames = resourceNames

