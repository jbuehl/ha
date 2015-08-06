
restTimeout = 60

import json
import requests
import urllib
import socket
from ha.HAClasses import *

class HARestInterface(HAInterface):
    def __init__(self, name, interface=None, event=None, service="", secure=False, cache=True):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.service = service  # the REST service to target
        self.secure = secure    # use SSL
        self.cache = cache      # cache the states
        self.enabled = True
        self.hostname = socket.gethostname()
        debug('debugRest', self.name, "created", self.hostname, self.secure)
        if self.secure:
            self.keyDir = keyDir
            self.crtFile = self.keyDir+self.hostname+"-client.crt"
            self.keyFile = self.keyDir+self.hostname+"-client.key"
            self.caFile = self.keyDir+"ca.crt"
            debug('debugRest', self.name, self.crtFile, self.keyFile, self.caFile)
        if self.cache:
            # start the thread to update the cache when states change
            def readStates():
                debug('debugRestStates', self.name, "readStates started")
                while self.enabled:
                    self.readStates("/resources/states/stateChange")
                    if self.event:
                        self.event.set()
                        debug('debugInterrupt', self.name, "event set")
            readStatesThread = threading.Thread(target=readStates)
            readStatesThread.start()

    # return the state value for the specified sensor address
    def read(self, addr):
        if self.cache:
            try:
                if self.states[addr] == None:
                    self.states[addr] = self.readState(addr)
                return self.states[addr]
            except:
                return self.readState(addr)
        else:
            return self.readState(addr)

    # load state values of all sensor addresses into the cache
    def readStates(self, addr="/resources/states/state"):
        states = self.readState(addr)
        debug('debugRestStates', self.name, "readStates", "states", states)
        for sensor in states.keys():
            try:
                self.states[self.sensors[sensor].addr] = states[sensor]
            except:
                debug('debugRestStates', self.name, "sensor not found", sensor)

    # return the state value of the specified sensor address       
    def readState(self, addr):
        debug('debugRestStates', self.name, "readState", addr)
        path = self.service+urllib.quote(addr)
        try:
            if self.secure:
                url = "https://"+path
                debug('debugRestGet', self.name, "GET", url)
                r = requests.get(url, timeout=restTimeout,
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                url = "http://"+path
                debug('debugRestGet', self.name, "GET", url)
                r = requests.get(url, timeout=restTimeout)
            debug('debugRestGet', self.name, "status", r.status_code)
            if r.status_code == 200:
                attr = addr.split("/")[-1]
                if (attr == "state") or (attr == "stateChange"):
                    return r.json()[attr]
                else:
                    return r.json()
            else:
                return {}
        except requests.exceptions.ReadTimeout: # timeout
            debug('debugRest', self.name, "timeout")
            self.enabled = False
            return {}
        except:                                 # other exceptions are fatal
            debug('debugRest', self.name, "disabled")
            self.enabled = False
            return {}

    def write(self, addr, value):
        path = self.service+urllib.quote(addr)
        try:
            if self.secure:
                url = "https://"+path
                debug('debugRestPut', self.name, "PUT", url)
                r = requests.put(url,
                                 headers={"content-type":"application/json"}, 
                                 data=json.dumps({addr.split("/")[-1]:value}),
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                url = "http://"+path
                debug('debugRestPut', self.name, "PUT", url)
                r = requests.put(url, 
                                 headers={"content-type":"application/json"}, 
                                 data=json.dumps({addr.split("/")[-1]:value}))
            debug('debugRestPut', self.name, "status", r.status_code)
            if r.status_code == 200:
                return True
            else:
                return False
        except:
            debug('debugRest', self.name, "disabled")
            self.enabled = False
            return False

