
from ha import *
from ha.rest.restConfig import *
from socketserver import ThreadingMixIn
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import threading
import socket
import time
import struct
import copy

# RESTful web services server interface
class RestServer(object):
    def __init__(self, name, resources=None, port=restServicePort, notify=True, event=None, label="", multicast=True):
        debug('debugRestServer', name, "creating RestServer")
        self.name = name
        self.resources = resources
        self.hostname = socket.gethostname()
        self.port = port
        self.notify = notify
        if event:
            self.event = event
        else:
            self.event = self.resources.event
        self.multicast = multicast
        if label == "":
            self.label = self.hostname+":"+str(self.port)
        else:
            self.label = label
        debug('debugInterrupt', self.label, "event", self.event)
        self.server = RestHTTPServer(('', self.port), RestRequestHandler, self.resources)
        if self.multicast:
            self.restAddr = multicastAddr
        else:
            self.restAddr = "<broadcast>"
        self.stateSocket = None
        self.stateSequence = 0

    def start(self):
        debug('debugRestServer', self.name, "starting RestServer")
        if self.notify:
            # start the thread to send the resource states periodically and also when one changes
            def stateNotify():
                debug('debugRestServer', self.name, "REST state started")
                resources = list(self.resources.keys())
                states = self.resources.getState()
                lastStates = states
                self.timeStamp = int(time.time())
                while True:
                    self.sendStateMessage(resources, states)
                    resources = None
                    states = None
                    # wait for either a state to change or the periodic trigger
                    currentStates = self.resources.getState(wait=True)
                    # compare the current states to the previous states
                    for sensor in list(lastStates.keys()):
                        try:
                            if currentStates[sensor] != lastStates[sensor]:
                                # a state changed
                                debug('debugRestState', self.name, sensor, lastStates[sensor], "-->", currentStates[sensor])
                                states = currentStates
                                self.timeStamp = int(time.time())
                                break
                        except KeyError:
                            # a resource was either added or removed
                            resources = list(self.resources.keys())
                            states = currentStates
                            self.timeStamp = int(time.time())
                            break
                    lastStates = currentStates
                debug('debugRestServer', self.name, "REST state ended")
            stateNotifyThread = threading.Thread(target=stateNotify)
            stateNotifyThread.start()

            # start the thread to trigger the keepalive message periodically
            def stateTrigger():
                debug('debugRestServer', self.name, "REST state trigger started", restBeaconInterval)
                while True:
                    debug('debugInterrupt', self.name, "trigger", "set", self.event)
                    self.event.set()
                    time.sleep(restBeaconInterval)
                debug('debugRestServer', self.name, "REST state trigger ended")
            stateTriggerThread = threading.Thread(target=stateTrigger)
            stateTriggerThread.start()

        # start the HTTP server
        self.server.serve_forever()

    def openSocket(self):
        msgSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        msgSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if self.multicast:
            msgSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                    struct.pack("4sl", socket.inet_aton(multicastAddr), socket.INADDR_ANY))
        else:
            msgSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return msgSocket

    def sendStateMessage(self, resources=None, states=None):
        stateMsg = {"service":{"name": self.name,
                               "hostname": self.hostname,
                               "port": self.port,
                               "label": self.label,
                               "timestamp": self.timeStamp,
                               "seq": self.stateSequence}}
        if resources:
            stateMsg["resources"] = resources
        if states:
            stateMsg["states"] = states
        if not self.stateSocket:
            self.stateSocket = self.openSocket()
        try:
            debug('debugRestState', self.name, str(list(stateMsg.keys())))
            self.stateSocket.sendto(bytes(json.dumps(stateMsg), "utf-8"),
                                                (self.restAddr, restNotifyPort))
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
            (resource, attr, query) = self.getResFromPath(self.server.resources, urllib.parse.unquote(self.path).lstrip("/").rstrip("/"))
            debug('debugRestGet', "resource:", resource, "attr:", attr, "query:", query)
            if resource:        # a valid resource was found
                self.send_response(200)     # success
                if attr:        # a resource attribute was specified
                    data = resource.__getattribute__(attr)
                    try:        # see if a content type is specified in the request
                        contentType = data["contentType"]
                        data = data["data"]
                    except:     # return a jsonised dictionary
                        contentType = "application/json"
                        data = json.dumps({attr:data})
                else:           # return the resource
                    contentType = "application/json"
                    try:
                        expand = False
                        if query:   # expand resources contained in this resource
                            if (query[0][0].lower() == "expand") and (query[0][1].lower() == "true"):
                                expand = True
                        data = json.dumps(resource.dump(expand))
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
        (resource, attr, query) = self.getResFromPath(self.server.resources, urllib.parse.unquote(self.path).lstrip("/"))
        debug('debugRestPut', "resource:", resource.name, "attr:", attr, "query:", query)
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
    def getResFromPath(self, resource, pathStr):
        pathItems = pathStr.split("?")
        path = pathItems[0]
        if len(pathItems) > 1:
            queryItems = pathItems[1].split("&")
            query = [queryItem.split("=") for queryItem in queryItems]
        else:
            query = None
        (name, sep, path) = path.partition("/")
        if name == resource.name:   # the path element matches the resource name so far
            if isinstance(resource, Collection):
                if sep == "":       # no more elements left in path
                    return (resource, None, query) # path matches collection
                else:
                    for res in list(resource.values()):
                        (matchRes, attr, query) = self.getResFromPath(res, path)
                        if matchRes:
                            return (matchRes, attr, query) # there was a match at a lower level
            else:
                if sep == "":       # no more elements left in path
                    return (resource, None, query) # path matches resource
                else:
                    (name, sep, path) = path.partition("/")
                    if sep == "":   # no more elements left in path
                        if name in dir(resource):
                            return (resource, name, query) # path matches resource and attr
        elif name in ["states", "resources"]:
            return (resource, name, query)
        return (None, None, query)         # no match
