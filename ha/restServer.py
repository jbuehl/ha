from ha.HAClasses import *
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import urllib
import threading
import socket
import ssl
import time
import copy

# Sensor that returns the states of all sensors in a list of resources
class ResourceStateSensor(HASensor):
    def __init__(self, name, interface, resources, event=None, addr=None, group="", type="sensor", location=None, view=None, label="", interrupt=None):
        HASensor.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt)
        self.resources = resources
        self.event = event
        self.states = {}

    def getState(self):
        for sensor in self.resources.values():
            if (sensor != self) and (sensor.type != "schedule"):
                self.states[sensor.name] = sensor.getState()
        if debugStateChange: log(self.name, "getState", self.states)
        return self.states

    def getStateChange(self):
        if debugInterrupt: log(self.name, "getStateChange")
        if self.event:
            self.event.clear()
            if debugInterrupt: log(self.name, "event clear", self.event)
            self.event.wait()
            if debugInterrupt: log(self.name, "event wait", self.event)
        else:
            time.sleep(10)
        lastState = copy.copy(self.states)
        newState = self.getState()
        if debugStateChange: log(self.name, "newState", newState)
        if debugStateChange: log(self.name, "lastState", lastState)
        changeState = {}
        for sensor in newState.keys():
            try:
                if debugStateChange: log(self.name, "sensor", sensor, "last", lastState[sensor], "new", newState[sensor])
                if newState[sensor] != lastState[sensor]:
                    changeState[sensor] = newState[sensor]
            except KeyError:
                changeState[sensor] = newState[sensor]
        if debugStateChange: log(self.name, "changeState", changeState)
        return changeState

# RESTful web services server interface
class RestServer(object):
    def __init__(self, resources, port=7378, beacon=True, event=None):
        self.resources = resources
        self.event = event
        self.resources.addRes(ResourceStateSensor("states", HAInterface("None"), self.resources, self.event))
        self.hostname = socket.gethostname()
        self.port = port
        self.beacon = beacon
        self.event = event
        self.server = RestHTTPServer(('', self.port), RestRequestHandler, self.resources)

    def start(self):
        if self.beacon:
            beacon = BeaconThread("beaconServer", self.port, self.resources)
            beacon.start()
        self.server.serve_forever()
        
class BeaconThread(threading.Thread):
    def __init__(self, name, port, resources):
        threading.Thread.__init__(self, target=self.doBeacon)
        self.name = name
        self.port = port
        self.hostname = socket.gethostname()
        self.resources = resources
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
    def doBeacon(self):
        if debugThread: log(self.name, "started")
        loopCount = 0
        beaconInterval = 10
        # wake up every second
        while running:
            # loop until the program state changes to not running
            if not running: break
            if loopCount == beaconInterval:
                self.socket.sendto(json.dumps((self.hostname, self.port, self.resources.dict())), ("<broadcast>", 4242))
                loopCount = 0
            loopCount += 1
            time.sleep(1)
        if debugThread: log(self.name, "terminated")

class RestHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, resources):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.resources = resources

class RestRequestHandler(BaseHTTPRequestHandler):
    serverVersion = "HARestHTTP/1.0"

    # return the attribute of the resource specified in the path
    def do_GET(self):
        if debugRestGet: log("path:", self.path)
        if debugRestGet: log("headers:", self.headers.__str__())
        (resource, attr) = self.getResFromPath(self.server.resources, urllib.unquote(self.path).lstrip("/"))
        if resource:
            self.send_response(200)     # success
            self.send_header("Content-type", "application/json")
            self.end_headers()
            if attr:    # return the specific attribute of the resource
                self.wfile.write(json.dumps({attr:resource.__getattribute__(attr)}))
            else:       # return all attributes of the resource
                self.wfile.write(json.dumps(resource.dict()))
        else:
            self.send_error(404)     # resource not found

    # set the attribute of the resource specified in the path to the value specified in the data
    def do_PUT(self):
        if debugRestPut: log("path:", self.path)
        if debugRestPut: log("headers:", self.headers.__str__())
        (resource, attr) = self.getResFromPath(self.server.resources, urllib.unquote(self.path).lstrip("/"))
        if resource:
            try:
                data = self.rfile.read(int(self.headers['Content-Length']))
                if debugRestPut: log("data:", data)
                if self.headers['Content-type'] == "application/json":
                    data = json.loads(data)
                resource.__setattr__(attr, data[attr])
                self.send_response(200) # success
                self.end_headers()
            except:
                self.send_error(500) # error
        else:
            self.send_error(404)     # resource not found


    # add a resource to the collection specified in the path using parameters specified in the data
    def do_POST(self):
        self.send_error(501)         # not implemented

    # delete the resource specified in the path from the collection
    def do_DELETE(self):
        self.send_error(501)         # not implemented

    # this suppresses logging from BaseHTTPServer
    def log_message(self, format, *args):
        return
        
    # Locate the resource or attribute specified by the path
    def getResFromPath(self, resource, path):
        (name, sep, path) = path.partition("/")
        if name == resource.name:   # the path element matches the resource name so far
            if isinstance(resource, HACollection):
                if sep == "":       # no more elements left in path
                    return (resource, None) # path matches collection
                else:
                    for res in resource.values():
                        (matchRes, attr) = self.getResFromPath(res, path)
                        if matchRes:
                            return (matchRes, attr) # there was a match at a lower level
            else:
                if sep == "":       # no more elements left in path
                    return (resource, None) # path matches resource
                else:
                    (name, sep, path) = path.partition("/")
                    if sep == "":   # no more elements left in path
                        if name in dir(resource):
                            return (resource, name) # path matches resource and attr
        return (None, None)         # no match

