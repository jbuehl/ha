import json
import requests
import urllib.request, urllib.parse, urllib.error
import socket
import threading
import sys
from ha import *
from ha.rest.restConfig import *

class RestInterface(Interface):
    def __init__(self, name, interface=None, event=None, serviceAddr="", secure=False, cache=True, writeThrough=True, stateChange=False):
        Interface.__init__(self, name, interface=interface, event=event)
        self.serviceAddr = serviceAddr      # address of the REST service to target (ipAddr:port)
        self.secure = secure                # use SSL
        self.cache = cache                  # cache the states
        self.writeThrough = writeThrough    # cache is write through
        self.stateChange = stateChange      # server supports getStateChange
        self.hostName = socket.gethostname()
        self.enabled = False
        debug('debugRest', self.name, "created", self.hostName, self.serviceAddr) #, self.secure, self.cache, self.enabled)
        if self.secure:
            self.keyDir = keyDir
            self.crtFile = self.keyDir+self.hostName+"-client.crt"
            self.keyFile = self.keyDir+self.hostName+"-client.key"
            self.caFile = self.keyDir+"ca.crt"
            debug('debugRest', self.name, self.crtFile, self.keyFile, self.caFile)

    def start(self):
        debug('debugRest', self.name, "starting")
        self.enabled = True
        if self.cache:
            if self.stateChange:
                readStateChangeThread = threading.Thread(target=self.readStateChange)
                readStateChangeThread.start()
            readStateNotifyThread = threading.Thread(target=self.readStateNotify)
            readStateNotifyThread.start()

    # thread to update the cache when the stateChange request returns
    def readStateChange(self):
        debug('debugRestStates', self.name, "readStateChange started")
        while self.enabled:
            states = self.readStates("/resources/states/stateChange")
            if states == {}:    # retry if there is an error
                debug('debugRestStates', self.name, "readStateChange error")
                time.sleep(restRetryInterval)
                debug('debugRestStates', self.name, "readStateChange retrying")
            else:
                self.notify()
        debug('debugRestStates', self.name, "readStateChange terminated")

    # thread to update the cache when a state notification message is received
    def readStateNotify(self):
        debug('debugRestStates', self.name, "readStateNotify started")
        # open the socket to listen for state change notifications
        debug('debugRest', self.name, "opening socket")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", restStatePort))
        while self.enabled:
            try:
                # wait to receive a state change notification message
                (data, addr) = self.socket.recvfrom(32768)
                msg = json.loads(data.decode("utf-8"))
                if addr[0]+":"+str(msg["port"]) == self.serviceAddr:   # is this from the correct service
                    debug('debugRestStates', self.name, "received state notification from", addr[0]+":"+str(msg["port"]), "matches serviceAddr", self.serviceAddr)
                    # this one is for us
                    debug('debugRestStates', self.name, "readStateNotify", "addr:", addr[0], "data:", data)
                    states = msg["state"]
                    debug('debugRestStates', self.name, "readStateNotify", "states", states)
                    # update the states
                    self.setStates(states)
                    self.notify()
                else:
                   debug('debugRestStates', self.name, "ignoring state notification from", addr[0]+":"+str(msg["port"]))
            except Exception as exception:
                # log and ignore exceptions
                log(self.name, "state notification exception", str(exception))
        # interface is no longer enabled
        self.stop()
        debug('debugRestStates', self.name, "readStateNotify terminated")

    def stop(self):
        if self.enabled:
            self.enabled = False
            debug('debugRest', self.name, "stopping")
            # invalidate the state cache
            for state in list(self.states.keys()):
                self.states[state] = None
            debug('debugRest', self.name, "closing socket")
            self.socket.close()

    # return the state value for the specified sensor address
    # addr is the REST path to the specified resource
    def read(self, addr):
        debug('debugRestStates', self.name, "read", addr)
        if not self.enabled:
            return None
        # read the state from the interface unless it is in the cache
        # or None is a valid value for this type of sensor - FIXME
        try:
            if (not self.cache) or ((self.states[addr] == None) and (self.sensorAddrs[addr].getStateType() != None)):
                # return the value from the cache if it is there
                    self.states[addr] = self.readRest(addr)["state"]
        except KeyError:
            self.states[addr] = None
        return self.states[addr]

    # get state values of all sensors on this interface
    def readStates(self, path="/resources/states/state"):
        debug('debugRestStates', self.name, "readStates", "path", path)
        # type of state resource: "state", "stateChange"
        stateType = path.split("/")[-1]
        try:
            states = self.readRest(path)[stateType]
        except KeyError:
            states = {}
        debug('debugRestStates', self.name, "readStates", "states", states)
        self.setStates(states)
        return states

    # set state values of all sensors into the cache
    def setStates(self, states):
        for sensor in list(states.keys()):
            self.states["/resources/"+sensor+"/state"] = states[sensor]

    # read the json data from the specified path and return a dictionary
    def readRest(self, path):
        debug('debugRestStates', self.name, "readRest", path)
        addrPath = self.serviceAddr+urllib.parse.quote(path)
        try:
            if self.secure:
                url = "https://"+addrPath
                debug('debugRestGet', self.name, "GET", url)
                response = requests.get(url, timeout=restTimeout,
                                 cert=(self.crtFile, self.keyFile),
                                 verify=False)
            else:
                url = "http://"+addrPath
                debug('debugRestGet', self.name, "GET", url)
                response = requests.get(url, timeout=restTimeout)
            debug('debugRestGet', self.name, "status", response.status_code)
            if response.status_code == 200:
                debug('debugRestGet', self.name, "response", response.json())
                return response.json()
            else:
                log(self.name, "read state status", response.status_code)
                return {}
        except requests.exceptions.Timeout:
            log(self.name, "read state timeout", path)
            return {}
        except Exception as exception:
            log(self.name, "read state exception", str(exception))
            return {}

    # write the control state to the specified address
    # addr is the REST path to the specified resource
    def write(self, addr, value):
        debug('debugRestStates', self.name, "write", addr, value)
        if self.cache:
            if self.writeThrough:
                # update the cache
                self.states[addr] = value
                self.notify()
            else:
                # invalidate the cache
                self.states[addr] = None
        # create a jsonized dictionary
        data=json.dumps({addr.split("/")[-1]:value})
        return self.writeRest(addr, data)

    # write json data to the specified path
    def writeRest(self, path, data):
        debug('debugRestStates', self.name, "writeRest", path, data)
        addrPath = self.serviceAddr+urllib.parse.quote(path)
        try:
            if self.secure:
                url = "https://"+addrPath
                debug('debugRestPut', self.name, "PUT", url, "data:", data)
                response = requests.put(url,
                                 headers={"content-type":"application/json"},
                                 data=data,
                                 cert=(self.crtFile, self.keyFile),
                                 verify=False)
            else:
                url = "http://"+addrPath
                debug('debugRestPut', self.name, "PUT", url, "data:", data)
                response = requests.put(url,
                                 headers={"content-type":"application/json"},
                                 data=data)
            debug('debugRestPut', self.name, "status", response.status_code)
            if response.status_code == 200:
                return True
            else:
                log(self.name, "write state status", response.status_code)
                return False
        except Exception as exception:
            log(self.name, "write state exception", str(exception))
            return False
