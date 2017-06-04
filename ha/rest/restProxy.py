
from ha import *
from ha.interfaces.restInterface import *
import json
import threading
import socket
import time

# Proxy for the resources exposed by one or more REST services

# Autodiscover services and resources
# Detect changes in resource configuration on each service
# Remove resources on services that don't respond

class RestProxy(threading.Thread):
    def __init__(self, name, resources, watch=[], ignore=[], event=None, lock=None):
        debug('debugRestProxy', name, "starting", name)
        debug('debugRestProxy', name, "watching", watch)    # watch == [] means watch all services
        debug('debugRestProxy', name, "ignoring", ignore)
        threading.Thread.__init__(self, target=self.doRest)
        self.name = name
        self.services = {}
        self.resources = resources
        self.lock = lock
        self.event = event
        self.cacheTime = 0
        self.watch = watch
        self.ignore = ignore
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
            if ((self.watch != []) and (serviceName  in self.watch)) or ((self.watch == []) and (serviceName not in self.ignore)):
                if serviceName not in self.services.keys():   # new service
                    debug('debugRestProxy', self.name, timeStamp, "adding", serviceName, serviceAddr, serviceTimeStamp, serviceLabel)
                    self.services[serviceName] = RestServiceProxy(serviceName, serviceAddr, serviceTimeStamp, 
                                                               RestInterface(serviceName, service=serviceAddr, event=self.event, secure=False),
                                                               label=serviceLabel, group="Services")
                    self.getResources(self.services[serviceName], serviceResources, serviceTimeStamp)
                    self.cacheTime = timeStamp
                    self.event.set()
                    debug('debugInterrupt', self.name, "event set")
                else:
                    if serviceTimeStamp > self.services[serviceName].timeStamp: # service resources changed
                        debug('debugRestProxy', self.name, timeStamp, "updating", serviceName, serviceAddr, serviceTimeStamp, serviceLabel)
                        if self.services[serviceName].enabled:
                            self.delResources(self.services[serviceName])
                        self.getResources(self.services[serviceName], serviceResources, serviceTimeStamp)
                        self.cacheTime = timeStamp
                        self.event.set()
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
                        self.event.set()
                        debug('debugInterrupt', self.name, "event set")
        debug('debugThread', self.name, "terminated")

    # get all the resources on the specified service and add them to the cache
    def getResources(self, service, serviceResources, timeStamp):
        debug('debugRestProxy', self.name, "getting", service.name)
        resources = Collection(service.name+"/Resources", aliases=self.resources.aliases)
        service.interface.enabled = True
        self.load(resources, service.interface, "/"+serviceResources["name"])
        service.resourceNames = resources.keys()
        service.timeStamp = timeStamp
        service.interface.readStates()          # fill the cache for these resources
        with self.lock:
            self.resources.addRes(service)
            self.resources.update(resources)
            del(resources)
        service.enabled = True

    # load resources from the specified interface
    # this does not replicate the collection hierarchy being read
    def load(self, resources, interface, path):
        node = interface.read(path)
        self.loadResource(resources, interface, node, path)
        if "resources" in node.keys():
            # the node is a collection
            for resource in node["resources"]:
                self.load(resources, interface, path+"/"+resource)

    # instantiate the resource from the specified node            
    def loadResource(self, resources, interface, node, path):
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
            # create the specified resource type
            try:
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
            except:
                log(self.name, "loadResource", interface.name, str(node), path, "exception")
                try:
                    if debugExceptions:
                        raise
                except NameError:
                    pass
            
    # delete all the resources from the specified service from the cache
    def delResources(self, service):
        service.enabled = False
        with self.lock:
            for resourceName in service.resourceNames:
                self.resources.delRes(resourceName)
            self.resources.delRes(service.name)

# proxy for a REST service
class RestServiceProxy(Sensor):
    def __init__(self, name, addr, timeStamp, interface, event=None, group="", type="service", location=None, view=None, label="", interrupt=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        debug('debugRestProxy', name, "created")
        self.name = name
        self.addr = addr
        self.timeStamp = timeStamp
        self.resourceNames = []
        self.interface = interface
#        self.className = "Sensor" # so the web UI doesn't think it's a control
        self.enabled = False

    def getState(self):
        return normalState(self.enabled)
        
    def __del__(self):
        del(self.interface)

