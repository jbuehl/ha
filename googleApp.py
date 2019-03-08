port = 4664
haUrl = "http://localhost:81/cmd/"
debug = True

from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import requests
import syslog

# convert a sensor name to a resource name
def convertName(name):
    words = name.split()
    result = words[0].lower()
    for word in words[1:]:
        result += word.capitalize()
    return result

# convert a value to a state that can be set
stateDict = {"Increase": "%5E", "Decrease": "v",
             "Raise": "Up", "Lower": "Down"}
def convertValue(value):
    try:
        return stateDict[value.capitalize()]
    except KeyError:
        try:
            return value.capitalize()
        except AttributeError:
            return state

# convert a display state to a phrase that makes sense when spoken
wordDict = {"f": "degrees",
            "c": "degrees",
            "in": "inches",
            "gpm": "gallons per minute",
            "kw": "kilowatts",
            "kwh": "kilowatt hours",
            "mwh": "megawatt hours",
            "v": "volts"
            }
def convertState(state):
    words = state.split()
    try:
        return words[0]+" "+wordDict[words[1].lower()]
    except (IndexError, KeyError):
        return state

# Google agent fulfillment server
class GoogleRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            request = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(request)
            action = data["queryResult"]["action"]
            parameters = data["queryResult"]["parameters"]
            if debug: syslog.syslog("action:"+action+" parameters:"+str(parameters))
            if action == "get":
                sensor = parameters["sensor"]
                url = haUrl+convertName(sensor)
            elif action == "set":
                control = parameters["control"]
                sensor = control
                if parameters["state"] != "":
                    value = convertValue(parameters["state"])
                elif parameters["number"] != "":
                    value = str(int(parameters["number"]))
                else:
                    self.sendResponse("What do you want to set "+control+" to?")
                    return
                url = haUrl+convertName(control)+"/"+value
            elif action == "query":
                control = parameters["control"]
                sensor = control
                url = haUrl+convertName(control)
                queryState = parameters["state"].capitalize()
            else:
                syslog.syslog("unrecognized action "+action)
                self.sendResponse("I don't know how to "+action)
                return
        except Exception as ex:
            syslog.syslog("Exception: "+str(ex))
            self.sendResponse("There's a bug in your code "+str(ex))
            return
        if debug: syslog.syslog(url)
        try:
            # execute the requested command and return the state
            reply = requests.get(url)
            state = reply.json()["state"]
            if action == "query":
                if state == queryState:
                    state = "Yes"
                else:
                    state = "No"
            if debug: syslog.syslog("state:"+state)
            self.sendResponse(sensor+(" are " if sensor[-1]=="s" else " is ")+convertState(state))
        except Exception as ex:
            syslog.syslog("exception: "+str(ex))
            self.sendResponse("Something didn't work "+str(ex))

    # build the webhook response
    # https://developers.google.com/actions/build/json/dialogflow-webhook-json
    def sendResponse(self, responseText):
        response = {"payload": {"google": {"expectUserResponse": False,
                                           "richResponse": {"items": [{"simpleResponse": {"textToSpeech": responseText}}]}
                                           }}}
        self.send_response(200) # success
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response))

    # this suppresses logging from BaseHTTPServer
    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    googleServer = HTTPServer(('', port), GoogleRequestHandler)
    googleServer.serve_forever()
