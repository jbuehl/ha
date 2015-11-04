
from ha.HAClasses import *
from ha.restInterface import *
from ha.restServer import *
from ha.restProxy import *
from ha.timeInterface import *
from haWeb import *

stateChangeEvent = threading.Event()
resourceLock = threading.Lock()


if __name__ == "__main__":
    # resources
    resources = HACollection("resources")

    # time resources
    timeInterface = TimeInterface("time")
    resources.addRes(HASensor("theDayOfWeek", timeInterface, "%A", type="date", group="Time", label="Day of week"))
    resources.addRes(HASensor("theDate", timeInterface, "%B %d %Y", type="date", group="Time", label="Date"))
    resources.addRes(HASensor("theTimeAmPm", timeInterface, "%I:%M %p", type="time", group="Time", label="Time"))
    resources.addRes(HASensor("sunrise", timeInterface, "sunrise", type="time", group="Time", label="Sunrise"))
    resources.addRes(HASensor("sunset", timeInterface, "sunset", type="time", group="Time", label="Sunset"))
    resources.addRes(HASensor("theDay", timeInterface, "%a %B %d %Y", type="date", label="Day"))
    resources.addRes(HASensor("theTime", timeInterface, "%I:%M", type="time", label="Time"))
    resources.addRes(HASensor("theAmPm", timeInterface, "%p", type="ampm", label="AmPm"))

    # start the cache to listen for services on other servers
    restCache = RestProxy("restProxy", resources, socket.gethostname()+":"+str(webRestPort), stateChangeEvent, resourceLock)
    restCache.start()
    
    # set up the web server
    webInit(resources, restCache)
    
    # start the REST server for this service
    restServer = RestServer(resources, port=webRestPort, event=stateChangeEvent)
    restServer.start()

