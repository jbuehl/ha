from ha import *
from ha.rest.restConfig import *
from ha.rest.restServiceProxy import *
from ha.interfaces.restInterface import *
import json
import threading
import socket
import time

# Proxy for the resources exposed by one or more REST services

# set default service port if not specified
def setServicePorts(serviceList):
    newServiceList = []
    for service in serviceList:
        if len(service.split(".")) < 2:
            service = "services."+service
        newServiceList.append(service)
    return newServiceList
    
def parseServiceData(data, addr):
    serviceData = json.loads(data)
    (serviceName, serviceAddr, serviceResources, serviceTimeStamp, serviceLabel, serviceStateChange, serviceSeq) = ("", "", [], 0, "", False, 0)
    # data is in list format
    if isinstance(serviceData, list):
        # service name
        try:
            serviceName = "services."+serviceData[5]
        except IndexError:
            serviceName = "services."+serviceData[0]    # use hostname
        serviceAddr = addr[0]+":"+str(serviceData[1])   # IPAddr:port
        serviceResources = serviceData[2]
        # timestamp and label are optional
        try:
            serviceTimeStamp = serviceData[3]
            serviceLabel = serviceData[4]
        except IndexError:
            serviceTimeStamp = 0
            serviceLabel = serviceName
        # does service support getStateChange
        try:
            serviceStateChange = serviceData[6]
        except IndexError:
            serviceStateChange = False
    # data is in dictionary format
    elif isinstance(serviceData, dict):
        try:
            serviceName = "services."+serviceData["name"]
            serviceAddr = addr[0]+":"+str(serviceData["port"])
            serviceResources = serviceData["resources"]
            serviceTimeStamp = serviceData["timestamp"]
            serviceLabel = serviceData["label"]
            serviceSeq = serviceData["seq"]
            serviceStateChange = serviceData["statechange"]
        except KeyError:
            pass
    return (serviceName, serviceAddr, serviceResources, serviceTimeStamp, serviceLabel, serviceStateChange, serviceSeq)
                        
# Autodiscover services and resources
# Detect changes in resource configuration on each service
# Remove resources on services that don't respond

class RestProxy(threading.Thread):
    def __init__(self, name, resources, watch=[], ignore=[], event=None, lock=None):
        debug('debugRestProxy', name, "starting", name)
        threading.Thread.__init__(self, target=self.restProxyThread)
        self.name = name
        self.services = {}                      # cached services
        self.resources = resources              # resource cache
        self.event = event
        self.cacheTime = 0                      # time of the last update to the cache
        self.watch = setServicePorts(watch)     # services to watch for
        self.ignore = setServicePorts(ignore)   # services to ignore
        self.ignore.append("services."+socket.gethostname()+":"+str(restServicePort))   # always ignore services on this host
        debug('debugRestProxy', name, "watching", self.watch)    # watch == [] means watch all services
        debug('debugRestProxy', name, "ignoring", self.ignore)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", restBeaconPort))

    def restProxyThread(self):
        debug('debugThread', self.name, "started")
        while running:
            # wait for a beacon message from a service
            (data, addr) = self.socket.recvfrom(8192)   # FIXME - need to handle arbitrarily large data
            debug('debugRestBeacon', self.name, "beacon data", data)
            # parse the message
            (serviceName, serviceAddr, serviceResources, serviceTimeStamp, serviceLabel, serviceStateChange, serviceSeq) = parseServiceData(data, addr)
            # rename it if there is an alias
            if serviceName in self.resources.aliases.keys():
                newServiceName = self.resources.aliases[serviceName]["name"]
                newServiceLabel = self.resources.aliases[serviceName]["label"]
                debug('debugRestProxy', self.name, "renaming", serviceName, "to", newServiceName)
                serviceName = newServiceName
                serviceLabel = newServiceLabel
#            timeStamp = time.time()
            # determine if this service should be processed based on watch and ignore lists
            if ((self.watch != []) and (serviceName  in self.watch)) or ((self.watch == []) and (serviceName not in self.ignore)):
                debug('debugRestProxy', self.name, "processing", serviceName, serviceAddr, serviceTimeStamp)
                if serviceName not in self.services.keys():
                    # create a new service proxy
                    debug('debugRestProxyAdd', self.name, "adding", serviceName, serviceAddr, serviceTimeStamp, serviceStateChange)
                    self.services[serviceName] = RestServiceProxy(serviceName, 
                                                                    RestInterface(serviceName+"Interface", 
                                                                                    serviceAddr=serviceAddr, 
                                                                                    event=self.event, 
                                                                                    secure=False, stateChange=serviceStateChange), 
                                                                    addr=0, 
                                                                    timeStamp=serviceTimeStamp, 
                                                                    label=serviceLabel, 
                                                                    group="Services")
                    service = self.services[serviceName]
                    service.enable()
                    self.getResources(service, serviceResources, serviceTimeStamp)
                else:   # service is already in the cache
                    service = self.services[serviceName]
                    service.cancelBeaconTimer("beacon received")
                    if not service.enabled:     # the service was previously disabled but it is broadcasting again
                        # re-enable it
                        debug('debugRestProxyDisable', self.name, "reenabling", serviceName, serviceAddr, serviceTimeStamp)
                        # update the resource cache
                        self.addResources(service)
                        service.interface.serviceAddr = serviceAddr # update the ipAddr:port in case it changed
                        service.enable()
                    if serviceTimeStamp > service.timeStamp: # service resources have changed
                        debug('debugRestProxyUpdate', self.name, "updating", serviceName, serviceAddr, serviceTimeStamp)
                        # delete the resources from the cache and get new resources for the service
                        self.delResources(service)
                        self.getResources(service, serviceResources, serviceTimeStamp)
                    else:   # no resource changes - skip it
                        debug('debugRestProxy', self.name, "skipping", serviceName, service.addr, serviceTimeStamp)
                service.startBeaconTimer()
                service.logSeq(serviceSeq)
            else:
                debug('debugRestProxy', self.name, "ignoring", serviceName, serviceAddr, serviceTimeStamp)

        debug('debugThread', self.name, "terminated")

    # get all the resources on the specified service and add to the cache
    def getResources(self, service, serviceResources, serviceTimeStamp):
        debug('debugRestProxy', self.name, "getting", service.name, "resources:", str(serviceResources))
        # load resources in a separate thread
        loadResourcesThread = threading.Thread(target=service.loadResources, args=(self, serviceResources, serviceTimeStamp,))
        loadResourcesThread.start()

    # add the resource of the service as well as 
    # all the resources from the specified service to the cache
    def addResources(self, service):
        debug('debugRestProxy', self.name, "adding resources for service", service.name)
        debug('debugRestLock', service.name, "locking")
        with self.resources.lock:
            self.resources.addRes(service)                  # the resource for the service
            self.resources.addRes(service.missedSeqSensor)  # missed beacon messages
            self.resources.update(service.resources)        # resources from the service
        debug('debugRestLock', service.name, "unlocking")
        self.cacheTime = service.timeStamp
        self.event.set()
        debug('debugInterrupt', self.name, "event set")

    # delete all the resources from the specified service from the cache
    # don't delete the resource of the service
    def delResources(self, service):
        debug('debugRestProxy', self.name, "deleting resources for service", service.name)
        debug('debugRestLock', service.name, "locking")
        with self.resources.lock:
            for resourceName in service.resourceNames:
                try:
                    self.resources.delRes(resourceName)
                except KeyError:
                    debug('debugRestProxy', service.name, "error deleting", resourceName)
        debug('debugRestLock', service.name, "unlocking")
        self.event.set()
        debug('debugInterrupt', self.name, "event set")


