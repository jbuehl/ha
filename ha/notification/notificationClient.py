
import requests
import urllib
import subprocess
from ha import *

def notify(notificationType, message):
    servers = subprocess.check_output("avahi-browse -tp --resolve _notification._tcp" ,shell=True).split("\n")
    if servers == [""]:
        log("notificationClient", "server not found")
    else:
        for server in servers:
            serverData = server.split(";")
            if len(serverData) > 6:
                host = serverData[6]
                port = serverData[8]
                url = "http://"+host+":"+port+"/notify?type="+notificationType+"&message="+urllib.quote(message)
                request = requests.get(url)
                if request.status_code != 200:
                    log("notificationClient", "error", url, request.status_code)
                break
