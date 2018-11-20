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
        try:
            serviceName = name.split(".")[1]
        except IndexError:
            serviceName = name
        self.missedSeqSensor = AttributeSensor(serviceName+"-missedSeq", None, None, self, "missedSeq")

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
        debug('debugRestSeq', "RestServiceProxy", self.name, seq, self.lastSeq, self.missedSeq)
        if seq == 0:
            self.lastSeq = 0    # reset when the service starts
        if self.lastSeq != 0:   # ignore the first one after this program starts
            self.missedSeq += seq - self.lastSeq - 1
        self.lastSeq = seq

    # define a timer to disable the interface if the beacon times out
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
                

