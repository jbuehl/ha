
import requests
import urllib.request, urllib.parse, urllib.error
import subprocess
from ha import *

def notify(notificationType, message):
    servers = subprocess.check_output("avahi-browse -tp --resolve _notification._tcp" ,shell=True).decode().split("\n")
    if servers == [""]:
        log("notificationClient", "server not found")
    else:
        for server in servers:
            serverData = server.split(";")
            if len(serverData) > 6:
                host = serverData[6]
                port = serverData[8]
                url = "http://"+host+":"+port+"/notify?eventType="+notificationType+"&message="+urllib.parse.quote(message)
                request = requests.get(url)
                if request.status_code != 200:
                    log("notificationClient", "error", url, request.status_code)
                break
