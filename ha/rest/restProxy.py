from ha import *
from ha.rest.restConfig import *
from ha.rest.restService import *
from ha.rest.restInterface import *
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
    debug('debugRestProxyData', "data", serviceData)
    (serviceName, serviceAddr, stateTimeStamp, resourceTimeStamp, serviceLabel, serviceSeq, serviceStates, serviceResources) = ("", "", 0, 0, "", 0, {}, [])
    try:
        try:
            serviceResources = serviceData["resources"]
        except KeyError:
            serviceResources = []
        try:
            serviceStates = serviceData["states"]
        except:
            serviceStates = {}
        serviceData = serviceData["service"]
        serviceName = "services."+serviceData["name"]
        serviceAddr = addr[0]+":"+str(serviceData["port"])
        try:
            stateTimeStamp = serviceData["statetimestamp"]
            resourceTimeStamp = serviceData["resourcetimestamp"]
        except KeyError:
            stateTimeStamp = serviceData["timestamp"]
            resourceTimeStamp = serviceData["timestamp"]
        serviceLabel = serviceData["label"]
        serviceSeq = serviceData["seq"]
    except Exception as ex:
        log("parseServiceData", type(ex).__name__, str(ex))
    return (serviceName, serviceAddr, stateTimeStamp, resourceTimeStamp, serviceLabel, serviceSeq, serviceStates, serviceResources)

# Autodiscover services and resources
# Detect changes in resource configuration on each service
# Remove resources on services that don't respond

class RestProxy(threading.Thread):
    def __init__(self, name, resources, watch=[], ignore=[], event=None, cache=True):
        debug('debugRestProxy', name, "starting", name)
        threading.Thread.__init__(self, target=self.restProxyThread)
        self.name = name
        self.services = {}                      # cached services
        self.resources = resources              # resource cache
        self.event = event
        self.cache = cache
        self.cacheTime = 0                      # time of the last update to the cache
        self.watch = setServicePorts(watch)     # services to watch for
        self.ignore = setServicePorts(ignore)   # services to ignore
        self.ignore.append("services."+socket.gethostname()+":"+str(restServicePort))   # always ignore services on this host
        debug('debugRestProxy', name, "watching", self.watch)    # watch == [] means watch all services
        debug('debugRestProxy', name, "ignoring", self.ignore)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((multicastAddr, restNotifyPort))

    def restProxyThread(self):
        debug('debugThread', self.name, "started")
        while True:
            # wait for a notification message from a service
            (data, addr) = self.socket.recvfrom(32768)   # FIXME - need to handle arbitrarily large data
            debug('debugRestMessage', self.name, "notification data", data)
            # parse the message
            (serviceName, serviceAddr, stateTimeStamp, resourceTimeStamp, serviceLabel, serviceSeq, serviceStates, serviceResources) = \
                parseServiceData(data.decode("utf-8"), addr)
            # rename it if there is an alias
            if serviceName in list(self.resources.aliases.keys()):
                newServiceName = self.resources.aliases[serviceName]["name"]
                newServiceLabel = self.resources.aliases[serviceName]["label"]
                debug('debugRestProxy', self.name, "renaming", serviceName, "to", newServiceName)
                serviceName = newServiceName
                serviceLabel = newServiceLabel
            # determine if this service should be processed based on watch and ignore lists
            if ((self.watch != []) and (serviceName  in self.watch)) or ((self.watch == []) and (serviceName not in self.ignore)):
                debug('debugRestProxy', self.name, "processing", serviceName, serviceAddr, stateTimeStamp, resourceTimeStamp)
                if serviceName not in list(self.services.keys()):
                    # this is one not seen before, create a new service proxy
                    debug('debugRestProxyAdd', self.name, "adding", serviceName, serviceAddr, stateTimeStamp, resourceTimeStamp)
                    self.services[serviceName] = RestService(serviceName,
                                                                RestInterface(serviceName+"Interface",
                                                                                serviceAddr=serviceAddr,
                                                                                event=self.event,
                                                                                cache=self.cache),
                                                                addr=0,
                                                                stateTimeStamp=stateTimeStamp,
                                                                resourceTimeStamp=resourceTimeStamp,
                                                                label=serviceLabel,
                                                                group="Services")
                    service = self.services[serviceName]
                    service.enable()
                    serviceResources = ["resources?expand=true"]
                    service.load(serviceResources, resourceTimeStamp)
                    self.addResources(service)
                    if serviceStates == {}:
                        serviceStates = service.interface.getStates()
                    service.stateTimeStamp = stateTimeStamp
                    self.resources.setStates(serviceStates)
                    self.resources.notify()
                else:   # service is already in the cache
                    service = self.services[serviceName]
                    service.cancelTimer("message received")
                    if not service.enabled:     # the service was previously disabled but it is broadcasting again
                        # re-enable it
                        debug('debugRestProxyDisable', self.name, "reenabling", serviceName, serviceAddr, stateTimeStamp, resourceTimeStamp)
                        # update the resource cache
                        self.addResources(service)
                        service.interface.serviceAddr = serviceAddr # update the ipAddr:port in case it changed
                        service.enable()
                    if (resourceTimeStamp > service.resourceTimeStamp) or (serviceResources != []):  # service resources have changed
                        debug('debugRestProxyUpdate', self.name, "updating", serviceName, serviceAddr, resourceTimeStamp)
                        # delete the resources from the cache and get new resources for the service
                        self.delResources(service)
                        serviceResources = ["resources?expand=true"]
                        service.load(serviceResources, resourceTimeStamp)
                        self.addResources(service)
                    if (stateTimeStamp > service.stateTimeStamp) or (serviceStates != {}): # states have changed
                        debug('debugRestProxyStates', self.name, "states", serviceName, serviceAddr, stateTimeStamp)
                        service.stateTimeStamp = stateTimeStamp
                        service.interface.setStates(serviceStates)     # load the interface cache
                        self.resources.setStates(serviceStates)             # update the resource collection cache
                        self.resources.notify()
                # start the message timer
                service.startTimer()
                service.logSeq(serviceSeq)
            else:
                debug('debugRestProxy', self.name, "ignoring", serviceName, serviceAddr, stateTimeStamp, resourceTimeStamp)
        debug('debugThread', self.name, "terminated")

    # add the resource of the service as well as
    # all the resources from the specified service to the cache
    def addResources(self, service):
        debug('debugRestProxy', self.name, "adding resources for service", service.name)
        self.resources.addRes(service)                          # the resource of the service
        self.resources.addRes(service.missedSeqSensor)          # missed messages
        self.resources.addRes(service.missedSeqPctSensor)       # percent of missed messages
        for resource in list(service.resources.values()):       # resources from the service
            self.resources.addRes(resource)
        self.cacheTime = service.resourceTimeStamp # FIXME
        self.event.set()
        debug('debugInterrupt', self.name, "event set")

    # delete all the resources from the specified service from the cache
    # don't delete the resource of the service
    def delResources(self, service):
        debug('debugRestProxy', self.name, "deleting resources for service", service.name)
        for resourceName in list(service.resources.keys()):
            try:
                self.resources.delRes(resourceName)
            except KeyError:
                debug('debugRestProxy', service.name, "error deleting", resourceName)
        self.event.set()
        debug('debugInterrupt', self.name, "event set")
