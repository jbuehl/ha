
from ha.HAClasses import *
from ha.restInterface import *
import json
import threading
import socket
import time

# Proxy for the resources exposed by one or more REST services

# Autodiscover services and resources
# Detect changes in resource configuration on each service
# Remove resources on services that don't respond

class RestProxy(threading.Thread):
    def __init__(self, name, resources, selfRest, stateChangeEvent, resourceLock):
        debug('debugRestProxy', name, "starting", name)
        debug('debugRestProxy', name, "ignoring", selfRest)
        threading.Thread.__init__(self, target=self.doRest)
        self.name = name
        self.services = {}
        self.resources = resources
        self.resourceLock = resourceLock
        self.stateChangeEvent = stateChangeEvent
        self.cacheTime = 0
        self.selfRest = selfRest
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", 4242))
                
    def doRest(self):
        debug('debugThread', self.name, "started")
        while running:
            (data, addr) = self.socket.recvfrom(4096)
            debug('debugRestBeacon', self.name, "beacon data", data)
            serviceData = json.loads(data)
            serviceName = serviceData[0]+":"+str(serviceData[1])       # hostname:port
            serviceAddr = addr[0]+":"+str(serviceData[1])             # IPAddr:port
            serviceResources = serviceData[2]
            try:
                serviceTimeStamp = serviceData[3]
                serviceLabel = serviceData[4]
            except:
                serviceTimeStamp = 0
                serviceLabel = serviceName
            timeStamp = time.time()
            if serviceName not in self.selfRest:   # ignore the beacon from this service
                if serviceName not in self.services.keys():   # new service
                    debug('debugRestProxy', self.name, timeStamp, "adding", serviceName, serviceAddr, serviceTimeStamp, serviceLabel)
                    self.services[serviceName] = RestServiceProxy(serviceName, serviceAddr, serviceTimeStamp, 
                                                               HARestInterface(serviceName, service=serviceAddr, event=self.stateChangeEvent, secure=False),
                                                               label=serviceLabel, group="Services")
                    self.getResources(self.services[serviceName], serviceResources, serviceTimeStamp)
                    self.cacheTime = timeStamp
                    self.stateChangeEvent.set()
                    debug('debugInterrupt', self.name, "event set")
                else:
                    if serviceTimeStamp > self.services[serviceName].timeStamp: # service resources changed
                        debug('debugRestProxy', self.name, timeStamp, "updating", serviceName, serviceAddr, serviceTimeStamp, serviceLabel)
                        if self.services[serviceName].enabled:
                            self.delResources(self.services[serviceName])
                        self.getResources(self.services[serviceName], serviceResources, serviceTimeStamp)
                        self.cacheTime = timeStamp
                        self.stateChangeEvent.set()
                        debug('debugInterrupt', self.name, "event set")
            for serviceName in self.services.keys():
                service = self.services[serviceName]
                if service.enabled:
                    if not service.interface.enabled:    # delete disabled service resources
                        debug('debugRestProxy', self.name, timeStamp, "disabling", serviceName, service.addr, service.timeStamp, service.label)
                        self.delResources(service)
                        del(self.services[service.name])
                        del(service)
                        self.cacheTime = timeStamp
                        self.stateChangeEvent.set()
                        debug('debugInterrupt', self.name, "event set")
        debug('debugThread', self.name, "terminated")

    # get all the resources on the specified service and add them to the cache
    def getResources(self, service, serviceResources, timeStamp):
        debug('debugRestProxy', self.name, "getting", service.name)
        resources = HACollection(service.name+"Resources", aliases=self.resources.aliases)
        service.interface.enabled = True
        resources.load(service.interface, "/"+serviceResources["name"])
        service.resourceNames = resources.keys()
        service.timeStamp = timeStamp
        service.interface.readStates()          # fill the cache for these resources
        with self.resourceLock:
            self.resources.addRes(service)
            self.resources.update(resources)
            del(resources)
        service.enabled = True

    # delete all the resources from the specified service from the cache
    def delResources(self, service):
        service.enabled = False
        with self.resourceLock:
            for resourceName in service.resourceNames:
                self.resources.delRes(resourceName)
            self.resources.delRes(service.name)

# proxy for a REST service
class RestServiceProxy(HASensor):
    def __init__(self, name, addr, timeStamp, interface, event=None, group="", type="service", location=None, view=None, label="", interrupt=None):
        HASensor.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        debug('debugRestProxy', name, "created")
        self.name = name
        self.addr = addr
        self.timeStamp = timeStamp
        self.resourceNames = []
        self.interface = interface
#        self.className = "HASensor" # so the web UI doesn't think it's a control
        self.enabled = False

    def getState(self):
        return normalState(self.enabled)
        
    def __del__(self):
        del(self.interface)

