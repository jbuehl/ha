from ha import *
from ha.rest.restConfig import *
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
        if len(service.split(":")) < 2:
            service = service+":"+str(restServicePort)
        newServiceList.append(service)
    return newServiceList
    
# Autodiscover services and resources
# Detect changes in resource configuration on each service
# Remove resources on services that don't respond

class RestProxy(threading.Thread):
    def __init__(self, name, resources, watch=[], ignore=[], event=None, lock=None):
        debug('debugRestProxy', name, "starting", name)
        threading.Thread.__init__(self, target=self.doRest)
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
                
    def doRest(self):
        debug('debugThread', self.name, "started")
        while running:
            # wait for a beacon message from a service
            (data, addr) = self.socket.recvfrom(8192)   # FIXME - need to handle arbitrarily large data
            debug('debugRestBeacon', self.name, "beacon data", data)
            # parse the message
            serviceData = json.loads(data)
            try:
                serviceName = "services."+serviceData[5]+":"+str(serviceData[1])
            except IndexError:
                serviceName = "services."+serviceData[0]+":"+str(serviceData[1])    # hostname:port
            serviceAddr = addr[0]+":"+str(serviceData[1])                       # IPAddr:port
            serviceResources = serviceData[2]
            # timestamp and label are optional
            try:
                serviceTimeStamp = serviceData[3]
                serviceLabel = serviceData[4]
            except IndexError:
                serviceTimeStamp = 0
                serviceLabel = serviceName
            # rename it if there is an alias
            if serviceName in self.resources.aliases.keys():
                newServiceName = self.resources.aliases[serviceName]["name"]
                newServiceLabel = self.resources.aliases[serviceName]["label"]
                debug('debugRestProxy', self.name, "renaming", serviceName, "to", newServiceName)
                serviceName = newServiceName
                serviceLabel = newServiceLabel
            timeStamp = time.time()
            # determine if this message should be processed
            if ((self.watch != []) and (serviceName  in self.watch)) or ((self.watch == []) and (serviceName not in self.ignore)):
                debug('debugRestProxy', self.name, "processing", serviceName, serviceAddr, serviceTimeStamp)
                if serviceName not in self.services.keys():
                    # create a new service proxy
                    debug('debugRestProxyAdd', self.name, "adding", serviceName, serviceAddr, serviceTimeStamp)
                    self.services[serviceName] = RestServiceProxy(serviceName, serviceAddr, 
                                                               RestInterface(serviceName, service=serviceAddr, event=self.event, secure=False),
                                                               serviceTimeStamp, label=serviceLabel, group="Services")
                    self.services[serviceName].enable()
                    self.getResources(self.services[serviceName], serviceResources, serviceTimeStamp, timeStamp)
                    debug('debugInterrupt', self.name, "event set")
                else:   # service is already in the cache
                    service = self.services[serviceName]
                    if serviceTimeStamp > service.timeStamp: # service resources have changed
                        debug('debugRestProxyUpdate', self.name, "updating", serviceName, serviceAddr, serviceTimeStamp)
                        if service.enabled:
                            # delete the resources from the cache
                            self.delResources(service)
                        else:
                            # the service was previously disabled but it is broadcasting again
                            # re-enable it
                            debug('debugRestProxyDisable', self.name, "reenabling", serviceName, service.addr, serviceTimeStamp)
                            service.enable()
                        # update the resource cache and set the event
                        self.getResources(service, serviceResources, serviceTimeStamp, timeStamp)
                        debug('debugInterrupt', self.name, "event set")
                    else:   # no resource changes - ignore it
                        debug('debugRestProxy', self.name, "skipping", serviceName, service.addr, serviceTimeStamp)
            else:
                debug('debugRestProxy', self.name, "ignoring", serviceName, serviceAddr, serviceTimeStamp)
            for serviceName in self.services.keys():
                service = self.services[serviceName]
                if service.enabled:
                    if not service.interface.enabled:
                        # the service interface is disabled due to a heartbeat timeout or exception
                        # delete the service resources and disable the service proxy
                        debug('debugRestProxyDisable', self.name, "disabling", serviceName, service.addr, serviceTimeStamp)
                        service.disable()
                        self.delResources(service)
                        self.cacheTime = timeStamp
                        self.event.set()
                        debug('debugInterrupt', self.name, "event set")
        debug('debugThread', self.name, "terminated")

    # get all the resources on the specified service and add them to the cache
    def getResources(self, service, serviceResources, serviceTimeStamp, timeStamp):
        debug('debugRestProxy', self.name, "getting", service.name) #, "resources:", serviceResources, isinstance(serviceResources, list))
        # load in a separate thread
        def loadResources():
            resources = Collection(service.name+"/Resources", aliases=self.resources.aliases)
            try:
                if isinstance(serviceResources, list):
                    for serviceResource in serviceResources:
                        self.loadPath(resources, service.interface, "/"+service.interface.read("/"+serviceResource)["name"])
                else:   # for backwards compatibility
                    self.loadPath(resources, service.interface, "/"+serviceResources["name"])
                service.resourceNames = resources.keys()    # FIXME - need to alias the names
                service.timeStamp = serviceTimeStamp
                service.interface.readStates()          # fill the cache for these resources
                debug('debugRestLock', service.name, "locking")
                with self.resources.lock:
                    self.resources.addRes(service)
                    self.resources.update(resources)
                debug('debugRestLock', service.name, "unlocking")
            except KeyError:
                service.disable()
            del(resources)
            self.cacheTime = timeStamp
            self.event.set()
        loadResourcesThread = threading.Thread(target=loadResources)
        loadResourcesThread.start()

    # load resources from the path on the specified interface
    # this does not replicate the collection hierarchy being read
    def loadPath(self, resources, interface, path):
        node = interface.read(path)
        self.loadResource(resources, interface, node, path)
        if "resources" in node.keys():
            # the node is a collection
            for resource in node["resources"]:
                self.loadPath(resources, interface, path+"/"+resource)

    # instantiate the resource from the specified node            
    def loadResource(self, resources, interface, node, path):
        debug('debugCollection', self.name, "loadResource", "node:", node)
        try:
            # ignore certain resource types
            if node["class"] not in ["Collection", "HACollection", "Schedule", "ResourceStateSensor", "RestServiceProxy"]:
                # override attributes with alias attributes if specified for the resource
                try:
                    aliasAttrs = resources.aliases[node["name"]]
                    debug('debugCollection', self.name, "loadResource", node["name"], "found alias")
                    for attr in aliasAttrs.keys():
                        node[attr] = aliasAttrs[attr]
                        debug('debugCollection', self.name, "loadResource", node["name"], "attr:", attr, "value:", aliasAttrs[attr])
                except KeyError:
                    debug('debugCollection', self.name, "loadResource", node["name"], "no alias")
                    pass
                # assemble the argument string
                argStr = ""
                for arg in node.keys():
                    if arg == "class":
                        className = node[arg]
                        if className == "HAControl":        # FIXME - temp until ESPs are changed
                            className = "Control"
                    elif arg == "interface":                # use the REST interface
                        argStr += "interface=interface, "
                    elif arg == "addr":                     # addr is REST path
                        argStr += "addr=path+'/state', "
                    elif arg == "schedTime":                # FIXME - need to generalize this for any class
                        argStr += "schedTime=SchedTime(**"+str(node["schedTime"])+"), "
                    elif isinstance(node[arg], str) or isinstance(node[arg], unicode):  # arg is a string
                        argStr += arg+"='"+node[arg]+"', "
                    else:                                   # arg is numeric or other
                        argStr += arg+"="+str(node[arg])+", "
                debug("debugCollection", "creating", className+"("+argStr[:-2]+")")
                exec("resource = "+className+"("+argStr[:-2]+")")
                resources.addRes(resource)
        except Exception as exception:
            log(self.name, "loadResource", interface.name, str(node), path, exception)
            try:
                if debugExceptions:
                    raise
            except NameError:
                pass
            
    # delete all the resources from the specified service from the cache
    def delResources(self, service):
        debug('debugRestLock', service.name, "locking")
        with self.resources.lock:
            for resourceName in service.resourceNames:
                try:
                    self.resources.delRes(resourceName)
                except KeyError:
                    debug('debugRestProxy', service.name, "error deleting", resourceName)
        debug('debugRestLock', service.name, "unlocking")

# proxy for a REST service
class RestServiceProxy(Sensor):
    def __init__(self, name, addr, interface, timeStamp=-1, event=None, group="", type="service", location=None, label="", interrupt=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt)
        debug('debugRestServiceProxy', "RestServiceProxy", name, "created")
        self.name = name
        self.addr = addr
        self.timeStamp = timeStamp
        self.resourceNames = []
        self.interface = interface
#        self.className = "Sensor" # so the web UI doesn't think it's a control
        self.enabled = False

    def getState(self):
        return normalState(self.enabled)

    def setState(self, state, wait=False):
        if state == 0:
            self.enable()
        else:
            self.disable()
        return True
        
    def enable(self):
        debug('debugRestServiceProxy', "RestServiceProxy", self.name, "enabled")
        self.interface.start()
        self.enabled = True

    def disable(self):
        debug('debugRestServiceProxy', "RestServiceProxy", self.name, "disabled")
        self.interface.stop()
        self.enabled = False
        self.timeStamp = -1
        
#    def __del__(self):
#        del(self.interface)

