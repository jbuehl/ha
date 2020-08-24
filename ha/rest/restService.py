from ha import *
from ha.rest.restConfig import *
import threading

messageTimeout = beaconTimeout

# proxy for a REST service
class RestService(Sensor):
    def __init__(self, name, interface, addr=None, stateTimeStamp=-1, resourceTimeStamp=-1, group="", type="service", location=None, label="", event=None):
        Sensor.__init__(self, name, interface, addr=addr, group=group, type=type, location=location, label=label, event=event)
        debug('debugRestService', "RestService", name, "created")
        self.stateTimeStamp = stateTimeStamp      # the last time the states were updated
        self.resourceTimeStamp = resourceTimeStamp      # the last time the resources were updated
        self.resources = None           # resources on this service
        self.enabled = False
        self.messageTimer = None
        self.lastSeq = 0                # the last message sequence number received
        self.missedSeq = 0              # count of how many missed messages for this service
        self.missedSeqPct = 0.0         # percentage of missed messages
        try:
            serviceName = name.split(".")[1]
        except IndexError:
            serviceName = name
        self.missedSeqSensor = AttributeSensor(serviceName+"-missedSeq", None, None, self, "missedSeq")
        self.missedSeqPctSensor = AttributeSensor(serviceName+"-missedSeqPct", None, None, self, "missedSeqPct")

    def getState(self, missing=None):
        return normalState(self.enabled)

    def setState(self, state, wait=False):
        if state:
            self.enable()
        else:
            self.disable()
        return True

    def enable(self):
        debug('debugRestService', "RestService", self.name, "enabled")
        self.interface.start()
        self.enabled = True

    def disable(self):
        debug('debugRestService', "RestService", self.name, "disabled")
        self.interface.stop()
        self.messageTimer = None
        self.enabled = False

    def addResources(self):
        self.resources = Collection(self.name+"/Resources")

    def delResources(self):
        if self.resources:
            del(self.resources)
            self.resources = None

    def logSeq(self, seq):
        debug('debugRestSeq', "RestService", self.name, seq, self.lastSeq, self.missedSeq, self.missedSeqPct)
        if seq == 0:
            self.lastSeq = 0    # reset when the service starts
            self.missedSeqPct = 0.0
        if self.lastSeq != 0:   # ignore the first one after this program starts
            self.missedSeq += seq - self.lastSeq - 1
        if seq > 0:
            self.missedSeqPct = float(self.missedSeq) / float(seq)
        self.lastSeq = seq

    # define a timer to disable the service if the message timer times out
    # can't use a socket timeout because multiple threads are using the same port
    def messageTimeout(self):
        debug('debugMessageTimer', self.name, "timer expired")
        debug('debugRestProxyDisable', self.name, "read message timeout")
        self.disable()

    # start the message timer
    def startTimer(self):
        if messageTimeout:
            self.messageTimer = threading.Timer(messageTimeout, self.messageTimeout)
            self.messageTimer.start()
            debug('debugMessageTimer', self.name, "timer started", messageTimeout, "seconds")

    # cancel the message timer
    def cancelTimer(self, reason=""):
        if self.messageTimer:
            self.messageTimer.cancel()
            debug('debugMessageTimer', self.name, "timer cancelled", reason)

    # load resources from the specified REST paths
    def load(self, serviceResources, resourceTimeStamp):
        self.delResources()
        self.addResources()
        try:
            for serviceResource in serviceResources:
                self.loadPath(self.resources, self.interface, "/"+serviceResource)
            self.resourceTimeStamp = resourceTimeStamp
        except KeyError:
            self.disable()

    # load resources from the path on the specified interface
    # this does not replicate the collection hierarchy being read
    def loadPath(self, resources, interface, path):
        debug('debugLoadService', self.name, "loadPath", "path:", path)
        resourceDict = interface.readRest(path)
        self.loadResource(resources, interface, path, resourceDict)
        try:
            if "resources" in list(resourceDict["args"].keys()):    # the resource is a collection
                for resource in resourceDict["args"]["resources"]:
                    if isinstance(resource, str):
                        self.loadPath(resources, interface, path+"/"+resource)
                    elif isinstance(resource, dict):
                        self.loadResource(resources, interface, path, resource)
                    else:
                        log(self.name, "unknown resource type", str(resource))
        except KeyError:    # old resource dict
            if "resources" in list(resourceDict.keys()):    # the resource is a collection
                for resource in resourceDict["resources"]:
                    self.loadPath(resources, interface, path+"/"+resource)

    # instantiate the resource from the specified dictionary
    def loadResource(self, resources, interface, path, resourceDict):
        debug('debugLoadService', self.name, "loadResource", "path:", path, "resourceDict:", resourceDict)
        try:
            # ignore certain resource types
            if resourceDict["class"] not in ["Collection", "Schedule", "RestService"]:
                resourceDict["args"]["interface"] = None
                resource = loadResource(resourceDict, globals())
                # replace the resource interface and addr with the REST interface and addr
                resource.interface = interface
                resource.interface.addSensor(resource)
                resource.addr = "/resources/"+resource.name+"/state"
                resources.addRes(resource)
        except Exception as ex:
            log(self.name, "loadResource", interface.name, "exception", str(resourceDict), type(ex).__name__, str(ex))
            try:
                if debugExceptions:
                    raise
            except NameError:
                pass
