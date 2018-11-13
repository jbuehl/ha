sendMetrics = True
logMetrics = True

metricsPrefix = "com.example.ha"
metricsHost = "metrics.example.com"
metricsPort = 2003
logDir = "/data/ha/"

import time
import socket
import threading
import json
from ha import *

def startMetrics(resourceStates):
    metricsThread = threading.Thread(target=sendMetrics, args=(resourceStates,))
    metricsThread.start()
    
def sendMetrics(resourceStates):
    debug("debugMetrics", "metrics thread started")
    lastDay = ""
    while True:
        # wait for a new set of states
        metrics = resourceStates.getStateChange()

        # log state deltas to a file
        if logMetrics:
            today = time.strftime("%Y%m%d")
            if today != lastDay:
                lastDay = today
                lastStates = {}
            logFileName = logDir+today+".json"
            changedStates = {}
            for metric in metrics.keys():
                try:
                    if metrics[metric] != lastStates[metric]:
                        changedStates[metric] = metrics[metric]
                except KeyError:
                    changedStates[metric] = metrics[metric]
            if changedStates != {}:
                lastStates.update(changedStates)
                debug("debugMetrics", "writing states to", logFileName)
                with open(logFileName, "a") as logFile:
                    logFile.write(json.dumps([time.time(), changedStates])+"\n")

        # send states to the metrics server        
        if sendMetrics:
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

