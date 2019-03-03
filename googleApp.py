from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import urllib
import threading
import socket
import ssl
import time
import struct
import pprint
import requests

def convertName(name):
    words = name.split()
    result = words[0].lower()
    for word in words[1:]:
        result += word.capitalize()
    return result

# Google agent fulfillment server
class GoogleServer(object):
    def __init__(self, name, port=4664):
        self.name = name
        self.port = port
        self.server = RestHTTPServer(('', self.port), RestRequestHandler,)

    def start(self):
        # start the HTTP server
        self.server.serve_forever()

class RestHTTPServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)

class RestRequestHandler(BaseHTTPRequestHandler):
    serverVersion = "HAGoogleHTTP/1.0"

    # return the attribute of the resource specified in the path
    def do_GET(self):
        self.send_error(501)         # not implemented

    # set the attribute of the resource specified in the path to the value specified in the data
    def do_PUT(self):
        self.send_error(501)         # not implemented

    # add a resource to the collection specified in the path using parameters specified in the data
    def do_POST(self):
        request = self.rfile.read(int(self.headers['Content-Length']))
        if True: #self.headers['Content-type'] == "application/json":
            data = json.loads(request)
            # pprint.pprint(data)
            action = data["queryResult"]["action"]
            parameters = data["queryResult"]["parameters"]
            url = "http://localhost:81/cmd/"
            error = False
            if action == "get":
                url += convertName(parameters["sensor"])
            elif action == "set":
                url += convertName(parameters["control"])+"/"+parameters["state"].capitalize()
            else:
                error = True
        if not error:
            print url
            reply = requests.get(url)
            state = reply.json()["state"]
            # build the webhook response
            # https://developers.google.com/actions/build/json/dialogflow-webhook-json
            response = {
              "payload": {
                "google": {
                  "expectUserResponse": False,
                  "richResponse": {
                    "items": [
                      {
                        "simpleResponse": {
                          "textToSpeech": state
                        }
                      }
                    ]
                  }
                },
              },
            }

            self.send_response(200) # success
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response))
        else:
            self.send_error(500) # error

    # delete the resource specified in the path from the collection
    def do_DELETE(self):
        self.send_error(501)         # not implemented

    # this suppresses logging from BaseHTTPServer
    # def log_message(self, format, *args):
    #     return

if __name__ == "__main__":
    google = GoogleServer("google")
    google.start()
