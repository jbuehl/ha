
import requests
import urllib
import subprocess
from ha import *

def notify(notificationType, message):
    notifyServer = subprocess.check_output("avahi-browse -tp --resolve _notification._tcp" ,shell=True).strip("\n").split(";")
    if notifyServer == [""]:
        log("notificationClient", "server not found")
    else:
        host = notifyServer[11]
        port = notifyServer[13]
        url = "http://"+host+":"+port+"/notify?type="+notificationType+"&message="+urllib.quote(message)
        request = requests.get(url)
        if request.status_code != 200:
            log("notificationClient", "error", url, request.status_code)
