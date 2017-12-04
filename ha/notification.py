# Notification

import requests
import urllib
import json
from twilio.rest import Client
from ha import *

twilioKey = keyDir+"twilio.key"

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
    

