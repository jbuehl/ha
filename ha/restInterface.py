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

    def read(self, theAddr):
        try:
            if self.secure:
                r = requests.get("https://"+self.interface+urllib.quote(theAddr),
                                 cert=("../keys/"+self.hostname+".crt", "../keys/"+self.hostname+".key"), 
                                 verify="../keys/ca.crt")
            else:
                r = requests.get("http://"+self.interface+urllib.quote(theAddr))
            if r.status_code == 200:
                return r.json()
            else:
                return {}
        except:
            return {}

    def write(self, theAddr, theValue):
        try:
            r = requests.put("http://"+self.interface+urllib.quote(theAddr), 
                             headers={"content-type":"application/json"}, 
                             data=json.dumps(theValue))
            if r.status_code == 200:
                return True
            else:
                return False
        except:
            return False

