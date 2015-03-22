import json
import requests
import urllib
import socket
from ha.HAClasses import *

class HARestInterface(HAInterface):
    def __init__(self, name, interface, secure=False):
        HAInterface.__init__(self, name, interface)
        self.hostname = socket.gethostname()
        self.secure = secure
        if debugRest: log(self.name, self.hostname, self.secure)
        if self.secure:
            self.keyDir = keyDir
            self.crtFile = self.keyDir+self.hostname+"-client.crt"
            self.keyFile = self.keyDir+self.hostname+"-client.key"
            self.caFile = self.keyDir+"ca.crt"
            if debugRest: log(self.name, self.crtFile, self.keyFile, self.caFile)
        self.sensors = {}   # sensors using this instance of the interface
        self.states = {}    # state cache

    # return the state value for the specified sensor address from the cache
    def read(self, addr):
        try:
            if self.states[addr] == None:
                self.states[addr] = self.readState(addr)
            return self.states[addr]
        except:
            return self.readState(addr)

    # load state values of all sensor addresses into the cache
    def readStates(self):
        states = self.readState("/resources/states/state")
        if debugRestStates: log(self.name, "readStates", states)
        for sensor in states.keys():
            try:
                self.states[self.sensors[sensor].addr] = states[sensor]
            except:
                if debug: log(self.name, "sensor not found", sensor)

    # load the state value of the specified sensor address intp the cache        
    def readState(self, addr):
        if debugRestStates: log(self.name, "readState", addr)
        url = self.interface+urllib.quote(addr)
        try:
            if self.secure:
                if debugRestGet: log(self.name, "GET", "https://"+url)
                r = requests.get("https://"+url,
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                if debugRestGet: log(self.name, "GET", "http://"+url)
                r = requests.get("http://"+url)
            if debugRestGet: log(self.name, "status", r.status_code)
            if r.status_code == 200:
                attr = addr.split("/")[-1]
                if attr == "state":
                    return r.json()[attr]
                else:
                    return r.json()
            else:
                return {}
        except:
            return {}

    def write(self, addr, value):
        url = self.interface+urllib.quote(addr)
        try:
            if self.secure:
                if debugRestPut: log(self.name, "PUT", "https://"+url)
                r = requests.put("https://"+url,
                                 headers={"content-type":"application/json"}, 
                                 data=json.dumps({addr.split("/")[-1]:value}),
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                if debugRestPut: log(self.name, "PUT", "http://"+url)
                r = requests.put("http://"+url, 
                                 headers={"content-type":"application/json"}, 
                                 data=json.dumps({addr.split("/")[-1]:value}))
            if debugRestPut: log(self.name, "status", r.status_code)
            if r.status_code == 200:
                return True
            else:
                return False
        except:
            return False

    def addSensor(self, sensor):
        self.sensors[sensor.name] = sensor
        self.states[sensor.addr] = None


