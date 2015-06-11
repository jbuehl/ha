
thingTimeout = 5
thingRetries = 3

import subprocess
import requests
from ha.HAClasses import *

class ThingInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.ipAddrs = {}

    def addSensor(self, sensor):
        HAInterface.addSensor(self, sensor)
        self.ipAddrs[sensor.addr] = self.getIpAddr(sensor.addr)

    def getIpAddr(self, addr):
        debug('debugThing', self.name, "getIpAddr", addr)
        try:
            ipAddr = subprocess.check_output("avahi-resolve-host-name %s.local|cut -f2"%(addr), shell=True).strip("\n")
        except:
            ipAddr = "0.0.0.0"
        debug('debugThing', self.name, "IpAddr", ipAddr)
        return ipAddr

    def read(self, addr):
        debug('debugThing', self.name, "read", addr)
        retries = thingRetries
        while retries > 0:
            try:
                url = "http://"+self.ipAddrs[addr]+"/"
                debug('debugThing', self.name, "url", url)
                reply = requests.get(url, timeout=thingTimeout)
                debug('debugThing', self.name, "reply", reply.text)
                return int(reply.json()["state"])
            except requests.exceptions.ConnectionError:
                debug('debugThing', self.name, "connection error")
                self.ipAddrs[addr] = self.getIpAddr(addr)
                retries -= 1
            except:
                return 0
        return 0

    def write(self, addr, value):
        debug('debugThing', self.name, "write", addr, value)
        try:
            url = "http://"+self.ipAddrs[addr]+"/state="+str(value)
            debug('debugThing', self.name, "url", url)
            reply = requests.put(url, timeout=thingTimeout)
            debug('debugThing', self.name, "reply", reply.text)
            if self.event:
                debug('debugInterrupt', self.name, "event set")
                self.event.set()
            return 1
        except:
            return 0

