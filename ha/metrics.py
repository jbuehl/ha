metricsPrefix = "com.example.ha"
metricsHost = "metrics.example.com"
metricsPort = 2003

import time
import socket
import threading
from ha import *

def startMetrics(resourceStates):
    metricsThread = threading.Thread(target=sendMetrics, args=(resourceStates,))
    metricsThread.start()
    
def sendMetrics(resourceStates):
    debug("debugMetrics", "metrics thread started")
    while True:
        metrics = resourceStates.getStateChange()
        debug("debugMetrics", "opening socket to", metricsHost, metricsPort)
        metricsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        metricsSocket.connect((metricsHost, metricsPort))
        for metric in metrics.keys():
            if metric != "states":
                msg = metricsPrefix+"."+metric.replace(" ", "_")+" "+str(metrics[metric])+" "+str(int(time.time()))
                debug("debugMetrics", msg)
                while msg != "":
                    try:
                        metricsSocket.send(msg+"\n")
                        msg = ""
                    except socket.error as exception:
                        log("socket error", exception)
                        time.sleep(10)
        if metricsSocket:
            debug("debugMetrics", "closing socket to", metricsHost)
            metricsSocket.close()
    debug("debugMetrics", "metrics thread terminated")

