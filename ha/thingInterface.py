
thingTimeout = 5

import requests
from ha.HAClasses import *

class ThingInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        try:
            debug('debugThing', self.name, "read", addr)
            url = "http://"+addr+"/"
            reply = requests.get(url, timeout=thingTimeout)
            debug('debugThing', self.name, "reply", reply.text)
            return int(reply.text)
        except:
            return 0

    def write(self, addr, value):
        try:
            debug('debugThing', self.name, "write", addr, value)
            url = "http://"+addr+"/state="+str(value)
            reply = requests.get(url, timeout=thingTimeout)
            debug('debugThing', self.name, "reply", reply.text)
            if self.event:
                debug('debugInterrupt', self.name, "event set")
                self.event.set()
            return 1
        except:
            return 0

