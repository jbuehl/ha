multicast = False

from ha import *
from ha.rest.restConfig import *
from socketserver import ThreadingMixIn
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import json
import urllib.request, urllib.parse, urllib.error
import threading
import socket
import ssl
import time
import struct
import copy

def openSocket():
    theSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    theSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if multicast:
        theSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                struct.pack("4sl", socket.inet_aton(multicastGroup), socket.INADDR_ANY))
    else:
        theSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return theSocket

# RESTful web services server interface
class RestServer(object):
    def __init__(self, name, resources=None, port=restServicePort, beacon=True, heartbeat=True, event=None, label="", stateChange=False):
        debug('debugRestServer', name, "creating RestServer")
        self.name = name
        self.resources = resources
        self.hostname = socket.gethostname()
        self.port = port
        self.beacon = beacon
        self.heartbeat = heartbeat
        self.event = event
        if label == "":
            self.label = self.hostname+":"+str(self.port)
        else:
            self.label = label
        self.stateChange = stateChange
        debug('debugInterrupt', self.label, "event", self.event)
        self.server = RestHTTPServer(('', self.port), RestRequestHandler, self.resources)
        if multicast:
            self.restAddr = multicastGroup
        else:
            self.restAddr = "<broadcast>"
        self.beaconSocket = None
        self.stateSocket = None
        self.stateSequence = 0
        self.stateResource = None

    def start(self):
        debug('debugRestServer', self.name, "starting RestServer")
        # start the beacon to advertise this service
        if self.beacon:
            self.timeStamp = time.time()
            def beacon():
                debug('debugRestServer', self.name, "REST beacon started")
                beaconSequence = 0
                while True:
                    debug('debugRestBeacon', self.name, "REST beacon")
                    if not self.beaconSocket:
                        self.beaconSocket = openSocket()
                    try:
                        self.beaconSocket.sendto(bytes(json.dumps({"hostname": self.hostname,
                                                             "port": self.port,
                                                             "resources": [self.server.resources.name],
                                                             "timestamp": self.timeStamp,
                                                             "label": self.label,
                                                             "name": self.name,
                                                             "statechange": self.stateChange,
                                                             "seq": beaconSequence}), "utf-8"),
                                                        (self.restAddr, restBeaconPort))
                    except socket.error as exception:
                        log("socket error", str(exception))
                        self.beaconSocket = None
                    beaconSequence += 1
                    time.sleep(restBeaconInterval)
                debug('debugRestServer', self.name, "REST beacon ended")
            beaconThread = threading.Thread(target=beacon)
            beaconThread.start()

        # # locate the state resource
        # try:
        #     self.stateResource = self.resources.getRes("states", dummy=False)
        # except:
        #     debug('debugRestHeartbeat', self.name, "created resource state sensor")
        #     self.stateResource = ResourceStateSensor("states", None, resources=self.resources, event=self.event)
        #     self.resources.addRes(self.stateResource)

        # start the thread to send the state of all resources when one changes
        if True: #self.event:
            def stateNotify():
                debug('debugRestServer', self.name, "REST state started")
                lastStates = copy.copy(self.resources.getState())
                while True:
                    debug('debugRestState', self.name, "REST state")
                    states = copy.copy(self.resources.getState())
                    somethingChanged = False
                    for sensor in list(lastStates.keys()):
                        try:
                            if states[sensor] != lastStates[sensor]:
                                debug('debugRestState', self.name, sensor, lastStates[sensor], "-->", states[sensor])
                                somethingChanged = True
                        except KeyError:
                            pass
                    if somethingChanged:
                        self.sendStateMessage()
                        lastStates = copy.copy(states)
                    time.sleep(10)
                debug('debugRestServer', self.name, "REST state ended")
            stateNotifyThread = threading.Thread(target=stateNotify)
            stateNotifyThread.start()

        # start the HTTP server
        self.server.serve_forever()

    def sendStateMessage(self):
        if not self.stateSocket:
            self.stateSocket = openSocket()
        try:
            self.stateSocket.sendto(bytes(json.dumps({"state": self.resources.states,
                                                    "hostname": self.hostname,
                                                    "port": self.port,
                                                    "seq": self.stateSequence}), "utf-8"),
                                                (self.restAddr, restStatePort))
            if (self.event) and (self.stateChange):
                # set the state event so the stateChange request returns
                debug('debugInterrupt', self.name, "heartbeat", "set", self.event)
                self.event.set()
        except socket.error as exception:
            log("socket error", str(exception))
            self.stateSocket = None
        self.stateSequence += 1


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
        if self.path == "/":    # no resource was specified
            self.send_response(200)     # success
            self.send_header("Content-type", "application/json")
            self.end_headers()
#            self.wfile.write(json.dumps({"resources": self.server.resources.name}))
            self.wfile.write(bytes(json.dumps([self.server.resources.name]), "utf-8"))
        else:                   # find the specified resource or attribute
            (resource, attr) = self.getResFromPath(self.server.resources, urllib.parse.unquote(self.path).lstrip("/").rstrip("/"))
            debug('debugRestGet', "resource:", resource, "attr:", attr)
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
                        data = json.dumps(resource.dump())
                    except Exception as exception:
                        debug('debugRestException', "restServer", self.path, str(exception))
                        data = "{}"
                        self.send_error(500)
                self.send_header("Content-type", contentType)
                self.end_headers()
                debug('debugRestGet', "data:", data)
                self.wfile.write(bytes(data, "utf-8"))
            else:
                self.send_error(404)     # resource not found

    # set the attribute of the resource specified in the path to the value specified in the data
    def do_PUT(self):
        debug('debugRestPut', "path:", self.path)
        debug('debugRestPut', "headers:", self.headers.__str__())
        (resource, attr) = self.getResFromPath(self.server.resources, urllib.parse.unquote(self.path).lstrip("/"))
        debug('debugRestPut', "resource:", resource.name, "attr:", attr)
        if resource:
            try:
                data = self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8")
                debug('debugRestPut', "data:", data)
                if self.headers['Content-type'] == "application/json":
                    data = json.loads(data)
                resource.__setattr__(attr, data[attr])
                self.send_response(200) # success
                self.end_headers()
            except Exception as exception:
                debug('debugRestException', "restServer", self.path, str(exception))
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
                    for res in list(resource.values()):
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
