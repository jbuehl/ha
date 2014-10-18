from ha.logging import *
from ha.HAClasses import *
from ha.HAConf import *
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import urllib
import threading
import socket
import ssl

# RESTful web services server interface

class RestServer(object):
    def __init__(self, resources, port=7378, secure=False, beacon=True):
        self.resources = resources
        self.hostname = socket.gethostname()
        self.port = port
        self.beacon = beacon
        self.server = RestHTTPServer(('', self.port), RestRequestHandler, self.resources)
        if secure:
            self.server.socket = ssl.wrap_socket (self.server.socket, 
                                                  #server_side=True,
                                                  ssl_version=ssl.PROTOCOL_TLSv1, 
                                                  cert_reqs=ssl.CERT_REQUIRED,
                                                  certfile="keys/"+self.hostname+".crt", 
                                                  keyfile="keys/"+self.hostname+".key", 
                                                  ca_certs="keys/ca.crt",
                                                  )

    def start(self):
        if self.beacon:
            beacon = BeaconThread("beaconServer", self.port, self.resources)
            beacon.start()
        self.server.serve_forever()
        
class BeaconThread(threading.Thread):
    """ Message handling thread.

    """
    def __init__(self, theName, port, resources):
        """ Initialize the thread."""        
        threading.Thread.__init__(self, target=self.doBeacon)
        self.name = theName
        self.port = port
        self.hostname = socket.gethostname()
        self.resources = resources
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
    def doBeacon(self):
        """ Message handling loop.
        """
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

class RestHTTPServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, resources):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.resources = resources

class RestRequestHandler(BaseHTTPRequestHandler):
    serverVersion = "HARestHTTP/1.0"

    # return the attribute of the resource specified in the path
    def do_GET(self):
        if debugRest: log(self.path)
        if debugRest: log(self.headers.__str__())
        (resource, attr) = self.getResFromPath(self.server.resources, urllib.unquote(self.path).lstrip("/"))
        if resource:
            self.send_response(200)     # success
            self.send_header("Content-type", "application/json")
            self.end_headers()
            if attr:    # return the specific attribute of the resource
                self.wfile.write(json.dumps(resource.__getattribute__(attr)))
            else:       # return all attributes of the resource
                self.wfile.write(json.dumps(resource.dict()))
        else:
            self.send_response(404)     # resource not found

    # set the attribute of the resource specified in the path to the value specified in the data
    def do_PUT(self):
        if debugRest: log(self.path)
        if debugRest: log(self.headers.__str__())
        (resource, attr) = self.getResFromPath(self.server.resources, urllib.unquote(self.path).lstrip("/"))
        if resource:
            try:
                data = self.rfile.read(int(self.headers['Content-Length']))
                if debugRest: log(data)
                if self.headers['Content-type'] == "application/json":
                    data = json.loads(data)
                resource.__setattr__(attr, data)
                self.send_response(200) # success
            except:
                self.send_response(500) # error
        else:
            self.send_response(404)     # resource not found


    # add a resource to the collection specified in the path using parameters specified in the data
    def do_POST(self):
        self.send_response(501)         # not implemented

    # delete the resource specified in the path from the collection
    def do_DELETE(self):
        self.send_response(501)         # not implemented

    # logging
    def log_message(self, format, *args):
       if debugRest: log(format%(args))

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
                        if hasattr(resource, name):
                            return (resource, name) # path matches resource and attr
        return (None, None)         # no match

