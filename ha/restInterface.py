import json
import requests
import urllib
from ha.HAClasses import *

class HARestInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)

    def read(self, theAddr):
        try:
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

