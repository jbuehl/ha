import json
import requests
import urllib
import socket
import threading
from ha import *
from ha.rest.restConfig import *

class RestInterface(Interface):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface=None, event=None, service="", secure=False, cache=True, writeThrough=True):
        Interface.__init__(self, name, interface=interface, event=event)
        self.service = service  # the REST service to target
        self.secure = secure    # use SSL
        self.cache = cache      # cache the states
        self.writeThrough = writeThrough
        self.hostname = socket.gethostname()
        self.enabled = False
        debug('debugRest', self.name, "created", self.hostname, self.service) #, self.secure, self.cache, self.enabled)
        if self.secure:
            self.keyDir = keyDir
            self.crtFile = self.keyDir+self.hostname+"-client.crt"
            self.keyFile = self.keyDir+self.hostname+"-client.key"
            self.caFile = self.keyDir+"ca.crt"
            debug('debugRest', self.name, self.crtFile, self.keyFile, self.caFile)

    def start(self):
        debug('debugRest', self.name, "starting")
        self.enabled = True
        if self.cache:
            # start the thread to update the cache when states change
            def readStateChange():
                debug('debugRestStates', self.name, "readStateChange started")
                while self.enabled:
                    states = self.readStates("/resources/states/stateChange")
                    if states == {}:    # give up if there is an error
                        break
                    self.notify()
                debug('debugRestStates', self.name, "readStateChange terminated")
            readStateChangeThread = threading.Thread(target=readStateChange)
            readStateChangeThread.start()
            # start the thread to update the cache when a state change notification is received
            def readStateNotify():
                debug('debugRestStates', self.name, "readStateNotify started")
                # open the socket to listen for state change notifications
                debug('debugRest', self.name, "opening socket")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind(("", restStatePort))
                # define a timer to disable the interface if the heartbeat times out
                # can't use a socket timeout because multiple threads are using the same port
                def readStateTimeout():
                    debug('debugRestStateTimer', self.name, "timer expired")
                    debug('debugRestDisable', self.name, "read state timeout")
                    debug('debugRest', self.name, "disabled")
                    self.enabled = False
                readStateTimer = None
                while self.enabled:
                    if True: #try:
                        # wait to receive a state change notification message
                        (data, addr) = self.socket.recvfrom(8192)
#                        debug('debugRestStates', self.name, "readStateNotify", "addr:", addr[0], "data:", data)
                        msg = json.loads(data)
                        if addr[0]+":"+str(msg["port"]) == self.service:   # is this from the correct service
                            # this one is for us
                            debug('debugRestStates', self.name, "readStateNotify", "addr:", addr[0], "data:", data)
                            if readStateTimer:
                                # cancel the timeout
                                readStateTimer.cancel()
                                debug('debugRestStateTimer', self.name, "timer cancelled")
                            states = msg["state"]
                            debug('debugRestStates', self.name, "readStateNotify", "states", states)
                            # if still enabled, do it again
                            if self.enabled:
                                # update the states
                                self.setStates(states)
                                self.notify()
                                # start the timer
                                readStateTimer = threading.Timer(restTimeout, readStateTimeout)
                                readStateTimer.start()
                                debug('debugRestStateTimer', self.name, "timer started", restTimeout, "seconds")
                    else: #except:
                        debug('debugRest', self.name, "disabled")
                        self.enabled = False
                        break
                # interface is no longer enabled, clean up
                if readStateTimer:
                    readStateTimer.cancel()
                self.stop()
                debug('debugRestStates', self.name, "readStateNotify terminated")
            readStateNotifyThread = threading.Thread(target=readStateNotify)
            readStateNotifyThread.start()

    def stop(self):
        if self.enabled:
            self.enabled = False
            debug('debugRest', self.name, "stopping")
            self.states = {}
            debug('debugRest', self.name, "closing socket")
            self.socket.close()
        
    # return the state value for the specified sensor address
    def read(self, addr):
        debug('debugRestStates', self.name, "read", addr)
        if self.cache:
            debug('debugRestStates', self.name, "states", self.states)
            try:
                if self.states[addr] == None:
                    if self.sensorAddrs[addr].getStateType() != None:
                        self.states[addr] = self.readState(addr)
                return self.states[addr]
            except:
                return self.readState(addr)
        else:
            return self.readState(addr)

    # load state values of all sensor addresses
    def readStates(self, addr="/resources/states/state"):
        states = self.readState(addr)
        debug('debugRestStates', self.name, "readStates", "states", states)
        self.setStates(states)
        return states

    # set state values of all sensor addresses into the cache
    def setStates(self, states):
        for sensor in states.keys():
            try:
                # set state using address because name may have been aliased
                self.states["/resources/"+sensor+"/state"] = states[sensor]
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
                response = requests.get(url, timeout=restTimeout,
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                url = "http://"+path
                debug('debugRestGet', self.name, "GET", url)
                response = requests.get(url, timeout=restTimeout)
            debug('debugRestGet', self.name, "status", response.status_code)
            if response.status_code == 200:
                attr = addr.split("/")[-1]
                if (attr == "state") or (attr == "stateChange"):
                    return response.json()[attr]
                else:
                    return response.json()
            else:
                return {}
        except requests.exceptions.Timeout: # timeout
            debug('debugRestDisable', self.name, "read timeout", path)
            self.enabled = False
            return {}
        except Exception as exception:                                 # other exceptions are fatal
            debug('debugRestDisable', self.name, "exception", path, exception)
            self.enabled = False
            return {}

    def write(self, addr, value):
        path = self.service+urllib.quote(addr)
        if self.cache:
            if self.writeThrough:
                # update the cache
                self.states[addr] = value
                self.notify()
            else:
                # invalidate the cache
                self.states[addr] = None
        data=json.dumps({addr.split("/")[-1]:value})
        try:
            if self.secure:
                url = "https://"+path
                debug('debugRestPut', self.name, "PUT", url, "data:", data)
                response = requests.put(url,
                                 headers={"content-type":"application/json"}, 
                                 data=data,
                                 cert=(self.crtFile, self.keyFile), 
                                 verify=False)
            else:
                url = "http://"+path
                debug('debugRestPut', self.name, "PUT", url, "data:", data)
                response = requests.put(url, 
                                 headers={"content-type":"application/json"}, 
                                 data=data)
            debug('debugRestPut', self.name, "status", response.status_code)
            if response.status_code == 200:
                return True
            else:
                return False
        except:
            debug('debugRest', self.name, "disabled")
            self.enabled = False
            return False

