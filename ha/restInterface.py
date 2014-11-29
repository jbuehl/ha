import json
import requests
import urllib
import socket
from ha.HAClasses import *

class HARestInterface(HAInterface):
    def __init__(self, theName, theInterface, secure=False):
        HAInterface.__init__(self, theName, theInterface)
        self.hostname = socket.gethostname()
        self.secure = secure
        if debugRest: log(self.name, self.hostname, self.secure)
        if self.secure:
            self.keyDir = "/root/keys/"
            self.crtFile = self.keyDir+self.hostname+"-client.crt"
            self.keyFile = self.keyDir+self.hostname+"-client.key"
            self.caFile = self.keyDir+"ca.crt"
            if debugRest: log(self.name, self.crtFile, self.keyFile, self.caFile)

    def read(self, theAddr):
        url = self.interface+urllib.quote(theAddr)
        try:
            if self.secure:
                if debugRest: log(self.name, "GET", "https://"+url)
                r = requests.get("https://"+url,
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                if debugRest: log(self.name, "GET", "http://"+url)
                r = requests.get("http://"+url)
            if debugRest: log(self.name, "status", r.status_code)
            if r.status_code == 200:
                attr = theAddr.split("/")[-1]
                if attr == "state":
                    return r.json()[attr]
                else:
                    return r.json()
            else:
                return {}
        except:
            return {}

    def write(self, theAddr, theValue):
        url = self.interface+urllib.quote(theAddr)
        try:
            if self.secure:
                if debugRest: log(self.name, "PUT", "https://"+url)
                r = requests.put("https://"+url,
                                 headers={"content-type":"application/json"}, 
                                 data=json.dumps({theAddr.split("/")[-1]:theValue}),
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                if debugRest: log(self.name, "PUT", "http://"+url)
                r = requests.put("http://"+url, 
                                 headers={"content-type":"application/json"}, 
                                 data=json.dumps({theAddr.split("/")[-1]:theValue}))
            if debugRest: log(self.name, "status", r.status_code)
            if r.status_code == 200:
                return True
            else:
                return False
        except:
            return False

