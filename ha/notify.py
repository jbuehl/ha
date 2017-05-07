import requests
import urllib
from twilio.rest import TwilioRestClient

# get the value of a variable from a file
def getValue(fileName):
    return json.load(open(fileName))
    
# send an sms notification
def smsNotify(numbers, message):
    smsClient = TwilioRestClient(getValue(smsSid), getValue(smsToken))
    smsFrom = notifyFromNumber
    for smsTo in numbers:
        smsClient.sms.messages.create(to=smsTo, from_=smsFrom, body=message)

# send an iOS app notification
def iosNotify(app, message):
    if app != "":
        requests.get("http://"+app+".appspot.com/notify?message="+urllib.quote(message))
    
