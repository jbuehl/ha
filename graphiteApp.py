ignoreServers = []
metricPrefix = "com.thebuehls.shadyglade.ha"
graphiteHost = "metrics.buehl.co"
graphitePort = 2003

import time
import socket
from ha import *
from ha.rest.restProxy import *

def openSocket(theHost, thePort, theSocket=None):
    if theSocket:
        debug("debugGraphite", "closing socket to", theHost, thePort)
        theSocket.close()
    debug("debugGraphite", "opening socket to", theHost, thePort)
    theSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    theSocket.connect((theHost, thePort))
    return theSocket

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    resources = Collection("resources")
    resourceStates = ResourceStateSensor("states", None, resources=resources, event=stateChangeEvent)
    restCache = RestProxy("restCache", resources, ignore=ignoreServers, event=stateChangeEvent)
    restCache.start()
    graphiteSocket = openSocket(graphiteHost, graphitePort)
    while True:
        metrics = resourceStates.getStateChange()
        for metric in metrics.keys():
            msg = metricPrefix+"."+metric.replace(" ", "_")+" "+str(metrics[metric])+" "+str(int(time.time()))
            debug("debugGraphiteMsg", msg)
            while msg != "":
                try:
                    graphiteSocket.send(msg+"\n")
                    msg = ""
                except socket.error as exception:
                    log("socket error", exception)
                    time.sleep(10)
                    graphiteSocket = openSocket(graphiteHost, graphitePort, graphiteSocket)

