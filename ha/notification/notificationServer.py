# Notification
serviceNotifyNumbers = []
serviceNotifyFrom = ""
spaNotifyNumbers = []
spaNotifyFrom = ""
doorbellNotifyNumbers = []
doorbellNotifyFrom = ""
doorNotifyNumbers = []
doorNotifyFrom = ""

import requests
import urllib.request, urllib.parse, urllib.error
import json
from twilio.rest import Client
from ha import *

twilioKey = keyDir+"twilio.key"
iftttKey = keyDir+"ifttt.key"

# send notifications
def notify(resources, notificationType, message):
    debug("debugNotification", "notification", notificationType, message)
    if resources.getRes(notificationType).getState():
        if resources.getRes("smsAlerts").getState():
            if notificationType == "alertServices":
                fromNumber = serviceNotifyFrom
                toNumbers = serviceNotifyNumbers
            elif notificationType == "alertSpa":
                fromNumber = spaNotifyFrom
                toNumbers = spaNotifyNumbers
            elif notificationType == "alertDoorbell":
                fromNumber = doorbellNotifyFrom
                toNumbers = doorbellNotifyNumbers
            elif notificationType == "alertDoors":
                fromNumber = doorNotifyFrom
                toNumbers = doorNotifyNumbers
            elif notificationType == "alertMotion":
                fromNumber = motionNotifyFrom
                toNumbers = motionNotifyNumbers
            smsNotify(fromNumber, toNumbers, message)
        if resources.getRes("appAlerts").getState():
            appNotify("", message)
        if resources.getRes("iftttAlerts").getState():
            iftttNotify(message)
    else:
        debug("debugNotification", "notification", notificationType, "not enabled")

# send an sms notification
def smsNotify(fromNumber, toNumbers, message):
    smsClient = Client(getValue(twilioKey, "sid"), getValue(twilioKey, "token"))
    for toNumber in toNumbers:
        debug("debugNotification", "SMS notify from", fromNumber, "to", toNumber)
        smsClient.messages.create(to=toNumber, from_=fromNumber, body=message)

# send an app notification
def appNotify(app, message):
    if app != "":
        debug("debugNotification", "app notify to", app)
        requests.get("http://"+app+".appspot.com/notify?message="+urllib.parse.quote(message))

# send an IFTTT notification
def iftttNotify(message):
    key = getValue(iftttKey, "key")
    debug("debugNotification", "IFTTT notify")
    url = "https://maker.ifttt.com/trigger/haEvent/with/key/"+key
    headers = {"Content-Type": "application/json"}
    value2 = ""
    value3 = ""
    data = json.dumps({"value1": message, "value2": value2, "value3": value3})
    req = requests.post(url, data=data, headers=headers)
