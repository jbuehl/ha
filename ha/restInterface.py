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
        self.sensors = {}
        self.states = {}

    def read(self, addr):
        try:
            if self.states[addr] == None:
                self.states[addr] = self.readState(addr)
            return self.states[addr]
        except:
            return self.readState(addr)

    def readStates(self):
        if debugRestStates: log(self.name, "readStates")
        for addr in self.states.keys():
            self.states[addr] = self.readState(addr)

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


