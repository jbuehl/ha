from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import json
import requests

# convert a sensor name to a resource name
def convertName(name):
    words = name.split()
    result = words[0].lower()
    for word in words[1:]:
        result += word.capitalize()
    return result

port = 4664
haUrl = "http://localhost:81/cmd/"

# Google agent fulfillment server
class GoogleRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            request = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(request)
            # pprint.pprint(data)
            action = data["queryResult"]["action"]
            parameters = data["queryResult"]["parameters"]
            print action, parameters
            if action == "get":
                url = haUrl+convertName(parameters["sensor"])
            elif action == "set":
                url = haUrl+convertName(parameters["control"])+"/"+parameters["state"].capitalize()
            elif action == "query":
                url = haUrl+convertName(parameters["control"])
                queryState = parameters["state"].capitalize()
        except:
            self.send_error(400) # error
            return
        print url
        try:
            reply = requests.get(url)
            state = reply.json()["state"]
            if action == "query":
                if state == queryState:
                    state = "Yes"
                else:
                    state = "No"
            print state
            # build the webhook response
            # https://developers.google.com/actions/build/json/dialogflow-webhook-json
            response = {"payload": {"google": {"expectUserResponse": False,
                                               "richResponse": {"items": [{"simpleResponse": {"textToSpeech": state}}]}
                                               }}}
            self.send_response(200) # success
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response))
        except:
            self.send_error(500) # error

    def do_GET(self):
        self.send_error(501)         # not implemented

    def do_PUT(self):
        self.send_error(501)         # not implemented

    def do_DELETE(self):
        self.send_error(501)         # not implemented

    # this suppresses logging from BaseHTTPServer
    # def log_message(self, format, *args):
    #     return

if __name__ == "__main__":
    googleServer = HTTPServer(('', port), GoogleRequestHandler)
    googleServer.serve_forever()
