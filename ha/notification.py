# Notification

import requests
import urllib
import json
from twilio.rest import Client
from ha import *

twilioKey = keyDir+"twilio.key"
iftttKey = keyDir+"ifttt.key"

# send an sms notification
def smsNotify(numbers, message):
    smsClient = Client(getValue(twilioKey, "sid"), getValue(twilioKey, "token"))
    smsFrom = notifyFromNumber
    for smsTo in numbers:
        smsClient.messages.create(to=smsTo, from_=smsFrom, body=message)

# send an iOS app notification
def iosNotify(app, message):
    if app != "":
        requests.get("http://"+app+".appspot.com/notify?message="+urllib.quote(message))

# send an IFTTT notification
def iftttNotify(event, value1="", value2="", value3=""):
    key = getValue(iftttKey, "key")
    url = "https://maker.ifttt.com/trigger/"+event+"/with/key/"+key
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"value1": value1, "value2": value2, "value3": value3})
    req = requests.post(url, data=data, headers=headers)
