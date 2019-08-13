from ha import *
from ha.rest.restConfig import *
import threading

# proxy for a REST service
class RestServiceProxy(Sensor):
    def __init__(self, name, interface, addr, timeStamp=-1, group="", type="service", location=None, label="", interrupt=None, event=None):
        Sensor.__init__(self, name, interface, addr, group=group, type=type, location=location, label=label, interrupt=interrupt, event=event)
        debug('debugRestServiceProxy', "RestServiceProxy", name, "created")
        self.timeStamp = timeStamp      # the last time this service was updated
        self.resourceNames = []         # resource names on this service
#        self.className = "Sensor" # so the web UI doesn't think it's a control
        self.resources = None           # resources on this service
        self.enabled = False
        self.beaconTimer = None
        self.lastSeq = 0                # the last beacon message sequence number received
        self.missedSeq = 0              # count of how many missed beacon messages for this service
        self.missedSeqPct = 0.0         # percentage of missed messages
        try:
            serviceName = name.split(".")[1]
        except IndexError:
            serviceName = name
        self.missedSeqSensor = AttributeSensor(serviceName+"-missedSeq", None, None, self, "missedSeq")
        self.missedSeqPctSensor = AttributeSensor(serviceName+"-missedSeqPct", None, None, self, "missedSeqPct")

    def getState(self):
        return normalState(self.enabled)

    def setState(self, state, wait=False):
        if state:
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
        self.beaconTimer = None
        self.enabled = False
#        self.timeStamp = -1

    def addResources(self):
        self.resources = Collection(self.name+"/Resources")

    def delResources(self):
        if self.resources:
            del(self.resources)
            self.resources = None

    def logSeq(self, seq):
        debug('debugRestSeq', "RestServiceProxy", self.name, seq, self.lastSeq, self.missedSeq, self.missedSeqPct)
        if seq == 0:
            self.lastSeq = 0    # reset when the service starts
            self.missedSeqPct = 0.0
        if self.lastSeq != 0:   # ignore the first one after this program starts
            self.missedSeq += seq - self.lastSeq - 1
        if seq > 0:
            self.missedSeqPct = float(self.missedSeq) / float(seq)
        self.lastSeq = seq

    # define a timer to disable the service if the beacon times out
    # can't use a socket timeout because multiple threads are using the same port
    def beaconTimeout(self):
        debug('debugBeaconTimer', self.name, "timer expired")
        debug('debugRestProxyDisable', self.name, "read beacon timeout")
        self.disable()

    # start the beacon timer
    def startBeaconTimer(self):
        if beaconTimeout:
            self.beaconTimer = threading.Timer(beaconTimeout, self.beaconTimeout)
            self.beaconTimer.start()
            debug('debugBeaconTimer', self.name, "timer started", beaconTimeout, "seconds")

    # cancel the beacon timer
    def cancelBeaconTimer(self, reason=""):
        if self.beaconTimer:
            self.beaconTimer.cancel()
            debug('debugBeaconTimer', self.name, "timer cancelled", reason)

    # load resources from the specified REST paths and add to the resources of the specified restProxy
    def loadResources(self, restProxy, serviceResources, serviceTimeStamp):
        self.delResources()
        self.addResources()
        try:
            for serviceResource in serviceResources:
                self.loadPath(self.resources, self.interface, "/"+serviceResource)
            self.resourceNames = self.resources.keys()    # FIXME - need to alias the names
            self.timeStamp = serviceTimeStamp
            self.interface.readStates()          # fill the cache for these resources
            restProxy.addResources(self)
        except KeyError:
            self.disable()

    # load resources from the path on the specified interface
    # this does not replicate the collection hierarchy being read
    def loadPath(self, resources, interface, path):
        debug('debugLoadResources', self.name, "loadPath", "path:", path)
        node = interface.readRest(path)
        self.loadResource(resources, interface, node, path)
        if "resources" in node.keys():
            # the node is a collection
            for resource in node["resources"]:
                self.loadPath(resources, interface, path+"/"+resource)

    # instantiate the resource from the specified node
    def loadResource(self, resources, interface, node, path):
        debug('debugLoadResources', self.name, "loadResource", "node:", node)
        try:
            # ignore certain resource types
            if node["class"] not in ["Collection", "HACollection", "Schedule", "ResourceStateSensor", "RestServiceProxy"]:
                # override attributes with alias attributes if specified for the resource
                try:
                    aliasAttrs = resources.aliases[node["name"]]
                    debug('debugLoadResources', self.name, "loadResource", node["name"], "found alias")
                    for attr in aliasAttrs.keys():
                        node[attr] = aliasAttrs[attr]
                        debug('debugLoadResources', self.name, "loadResource", node["name"], "attr:", attr, "value:", aliasAttrs[attr])
                except KeyError:
                    debug('debugLoadResources', self.name, "loadResource", node["name"], "no alias")
                    pass
                # assemble the argument string
                argStr = ""
                for arg in node.keys():
                    if arg == "class":
                        className = node[arg]
                    elif arg == "interface":                # use the REST interface
                        argStr += "interface=interface, "
                    elif arg == "addr":                     # addr is REST path
                        argStr += "addr=path+'/state', "
                    elif arg == "schedTime":                # FIXME - need to generalize this for any class
                        argStr += "schedTime=SchedTime(**"+str(node["schedTime"])+"), "
                    elif arg == "cycleList":                # FIXME - need to generalize this for any class
                        argStr += "cycleList=["
                        for cycle in node["cycleList"]:
                            argStr += "Cycle(**"+str(cycle)+"), "
                        argStr += "], "
                    elif isinstance(node[arg], str) or isinstance(node[arg], unicode):  # arg is a string
                        argStr += arg+"='"+node[arg]+"', "
                    else:                                   # arg is numeric or other
                        argStr += arg+"="+str(node[arg])+", "
                debug("debugLoadResources", "creating", className+"("+argStr[:-2]+")")
                exec("resource = "+className+"("+argStr[:-2]+")")
                resources.addRes(resource)
        except Exception as exception:
            log(self.name, "loadResource", interface.name, "exception", str(node), path, str(exception))
            try:
                if debugExceptions:
                    raise
            except NameError:
                pass
