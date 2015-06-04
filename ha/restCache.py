
from ha.HAClasses import *
from ha.restInterface import *
import json
import threading
import socket
import time

# Cache of resource states for one or more REST servers

# Autodiscover servers and resources
# Detect changes in resources on each server
# Remove resources on servers that don't respond

class RestCache(threading.Thread):
    def __init__(self, name, resources, selfRest, stateChangeEvent, resourceLock):
        debug('debugRestCache', name, "starting", selfRest)
        threading.Thread.__init__(self, target=self.doRest)
        self.name = name
        self.servers = {}
        self.resources = resources
        self.resourceLock = resourceLock
        self.stateChangeEvent = stateChangeEvent
        self.cacheTime = 0
        self.selfRest = selfRest
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("", 4242))
                
    def doRest(self):
        debug('debugThread', self.name, "started")
        while running:
            (data, addr) = self.socket.recvfrom(4096)
            debug('debugRestBeacon', self.name, "beacon data", data)
            serverData = json.loads(data)
            serverName = serverData[0]+":"+str(serverData[1])       # hostname:port
            serverAddr = addr[0]+":"+str(serverData[1])             # IPAddr:port
            serverResources = serverData[2]
            try:
                serverTimeStamp = serverData[3]
                serverLabel = serverData[4]
            except:
                serverTimeStamp = 0
                serverLabel = serverName
            timeStamp = time.time()
            if serverName != self.selfRest:   # ignore the beacon from this service
                if serverName not in self.servers.keys():   # new server
                    debug('debugRestCache', self.name, timeStamp, "adding", serverName, serverAddr, serverTimeStamp)
                    self.servers[serverName] = RestCacheServer(serverName, serverAddr, serverTimeStamp, 
                                                               HARestInterface(serverName, server=serverAddr, event=self.stateChangeEvent, secure=False),
                                                               label=serverLabel, group="Servers")
                    self.getResources(self.servers[serverName], serverResources, serverTimeStamp)
                    self.cacheTime = timeStamp
                    self.stateChangeEvent.set()
                    debug('debugInterrupt', self.name, "event set")
                else:
                    if serverTimeStamp > self.servers[serverName].timeStamp: # server resources changed
                        debug('debugRestCache', self.name, timeStamp, "updating", serverName, serverAddr, serverTimeStamp)
                        self.delResources(self.servers[serverName])
                        self.getResources(self.servers[serverName], serverResources, serverTimeStamp)
                        self.cacheTime = timeStamp
                        self.stateChangeEvent.set()
                        debug('debugInterrupt', self.name, "event set")
            for serverName in self.servers.keys():
                if not self.servers[serverName].interface.enabled:    # delete disabled servers and their resources
                    debug('debugRestCache', self.name, timeStamp, "deleting", serverName)
                    self.delResources(self.servers[serverName])
                    del(self.servers[serverName])
                    self.cacheTime = timeStamp
                    self.stateChangeEvent.set()
                    debug('debugInterrupt', self.name, "event set")
        debug('debugThread', self.name, "terminated")

    # get all the resources on the specified server and add them to the cache
    def getResources(self, server, serverResources, timeStamp):
        debug('debugRestCache', self.name, "getting", server.name)
        resources = HACollection(server.name+"Resources")
        resources.load(server.interface, "/"+serverResources["name"])
        server.resourceNames = resources.keys()
        server.timeStamp = timeStamp
        server.interface.readStates()          # fill the cache for these resources
        with self.resourceLock:
            self.resources.addRes(server)
            self.resources.update(resources)
            del(resources)

    # delete all the resources from the specified server from the cache
    def delResources(self, server):
        with self.resourceLock:
            for resourceName in server.resourceNames:
                self.resources.delRes(resourceName)

# REST server that is being cached
class RestCacheServer(HASensor):
    def __init__(self, name, addr, timeStamp, interface, event=None, group="", type="sensor", location=None, view=None, label="", interrupt=None):
        HASensor.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        debug('debugRestCache', name, "created")
        self.name = name
        self.addr = addr
        self.timeStamp = timeStamp
        self.resourceNames = [name]
        self.interface = interface
        self.className = "HASensor" # so the web UI doesn't think it's a control

    def getViewState(self, views):
        return "Up"
        
    def __del__(self):
        del(self.interface)

