
import threading
from ha import *
from ha.interfaces.osInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    resources = Collection("resources", event=stateChangeEvent)

    osInterface = OSInterface("osInterface")
    resources.addRes(Sensor("system."+hostname+".cpuTemp", osInterface, "cpuTemp", type="tempC", group="System", label=hostname+" CPU temp"))
    resources.addRes(Sensor("system."+hostname+".cpuLoad", osInterface, "cpuLoad", type="pct", group="System", label=hostname+" CPU load"))
    resources.addRes(Sensor("system."+hostname+".uptime", osInterface, "uptime", group="System", label=hostname+" Uptime"))
    resources.addRes(Sensor("system."+hostname+".ipAddr", osInterface, "ipAddr eth0", group="System", label=hostname+" IP address"))

    restServer = RestServer("house", resources, label=hostname, event=stateChangeEvent)
    restServer.start()
