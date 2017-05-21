
restBeaconPort = 4242
restStatePort = 4243
restBeaconInterval = 10
restHeartbeatInterval = 30

from ha import *
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import urllib
import threading
import socket
import ssl
import time

# RESTful web services server interface
class RestServer(object):
    def __init__(self, resources, port=7378, beacon=True, heartbeat=True, event=None, label=""):
        self.label = label
        self.resources = resources
        self.event = event
        self.hostname = socket.gethostname()
        self.port = port
        self.beacon = beacon
        self.heartbeat = heartbeat
        self.event = event
        debug('debugInterrupt', self.label, "event", self.event)
        self.server = RestHTTPServer(('', self.port), RestRequestHandler, self.resources)

    def start(self):
        # start the beacon
        if self.beacon:
            self.beaconSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.beaconSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.beaconSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.timeStamp = time.time()
            def beacon():
                debug('debugRestBeacon', "REST beacon started")
                while True:
                    debug('debugRestBeacon', "REST beacon")
                    self.beaconSocket.sendto(json.dumps((self.hostname, self.port, self.resources.dict(), self.timeStamp, self.label)), ("<broadcast>", restBeaconPort))
                    time.sleep(restBeaconInterval)
            beaconThread = threading.Thread(target=beacon)
            beaconThread.start()
            
        # start the heartbeat
        if self.heartbeat:
            debug('debugRestHeartbeat', "REST heartbeat started")
            # thread to periodically send states as keepalive message
            self.heartbeatSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.heartbeatSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.heartbeatSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                stateResource = self.resources.getRes("states", dummy=False)
            except:
                debug('debugRestHeartbeat', "created resource state sensor")
                stateResource = ResourceStateSensor("states", None, resources=self.resources, event=self.event)
                self.resources.addRes(stateResource)
            def heartbeat():
                while True:
                    debug('debugRestHeartbeat', "REST heartbeat")
                    states = stateResource.states
                    # send the broadcast message
                    self.heartbeatSocket.sendto(json.dumps({"state": states, "hostname": self.hostname, "port": self.port}), ("<broadcast>", restStatePort))
                    # set the state event so the stateChange request returns
                    debug('debugInterrupt', "heartbeat", "set", self.event)
                    self.event.set()
                    time.sleep(restHeartbeatInterval)
            heartbeatThread = threading.Thread(target=heartbeat)
            heartbeatThread.start()
            
        # start the HTTP server
        self.server.serve_forever()

# Beacon that advertises this service        
class BeaconThread(threading.Thread):
    def __init__(self, name, port, resources, label):
        threading.Thread.__init__(self, target=self.doBeacon)
        self.name = name
        self.port = port
        self.hostname = socket.gethostname()
        self.resources = resources
        self.label = label
        self.beaconSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.beaconSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.beaconSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.timeStamp = time.time()
        
    def doBeacon(self):
        debug('debugThread', self.name, "started")
        loopCount = 0
        # wake up every second
        while running:
            # loop until the program state changes to not running
            if not running: break
            if loopCount == restBeaconInterval:
                self.beaconSocket.sendto(json.dumps((self.hostname, self.port, self.resources.dict(), self.timeStamp, self.label)), ("<broadcast>", restBeaconPort))
                loopCount = 0
            loopCount += 1
            time.sleep(1)
        debug('debugThread', self.name, "terminated")

class RestHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, resources):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.resources = resources

class RestRequestHandler(BaseHTTPRequestHandler):
    serverVersion = "HARestHTTP/1.0"

    # return the attribute of the resource specified in the path
    def do_GET(self):
        debug('debugRestGet', "path:", self.path)
        debug('debugRestGet', "headers:", self.headers.__str__())
        (resource, attr) = self.getResFromPath(self.server.resources, urllib.unquote(self.path).lstrip("/"))
        if resource:
            self.send_response(200)     # success
            if attr:    # determine the content type of the attribute of the resource
                data = resource.__getattribute__(attr)
                try:                    # see if the content type is specified
                    contentType = data["contentType"]
                    data = data["data"]
                except:                 # return a jsonised dictionary
                    contentType = "application/json"
                    data = json.dumps({attr:data})
            else:
                contentType = "application/json"
                try:
                    data = json.dumps(resource.dict())
                except:
                    data = ""
                    self.send_error(500)
            self.send_header("Content-type", contentType)
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)     # resource not found

    # set the attribute of the resource specified in the path to the value specified in the data
    def do_PUT(self):
        debug('debugRestPut', "path:", self.path)
        debug('debugRestPut', "headers:", self.headers.__str__())
        (resource, attr) = self.getResFromPath(self.server.resources, urllib.unquote(self.path).lstrip("/"))
        if resource:
            try:
                data = self.rfile.read(int(self.headers['Content-Length']))
                debug('debugRestPut', "data:", data)
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
            if isinstance(resource, Collection):
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
