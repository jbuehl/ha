
metricsPrefix = "com.example.ha"
metricsHost = "metrics.example.com"
metricsPort = 2003
logDir = "/data/ha/"

import time
import socket
import threading
import json
from ha import *

def startMetrics(resourceStates, sendMetrics, logMetrics, logChanged=True):

    def sendMetricsThread(resourceStates):
        debug("debugMetrics", "sendMetrics", "metrics thread started")
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
                for metric in list(metrics.keys()):
                    try:
                        # log the metric unless logChanged is True and if it has not changed from the last time
                        if (not logChanged) or (metrics[metric] != lastStates[metric]):
                            changedStates[metric] = metrics[metric]
                    except KeyError:
                        # this is the first time the metric has appeared
                        changedStates[metric] = metrics[metric]
                if changedStates != {}:
                    lastStates.update(changedStates)
                    debug("debugMetrics", "sendMetrics", "writing states to", logFileName)
                    with open(logFileName, "a") as logFile:
                        logFile.write(json.dumps([time.time(), changedStates])+"\n")

            # send states to the metrics server
            if sendMetrics:
                debug("debugMetrics", "sendMetrics", "opening socket to", metricsHost, metricsPort)
                try:
                    metricsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    metricsSocket.connect((metricsHost, metricsPort))
                    debug("debugMetrics", "sendMetrics", "sending", len(metrics), "metrics")
                    for metric in list(metrics.keys()):
                        if metric != "states":
                            if metric.split(".")[0] != "loads":
                                if metric.split(".")[0] in ["loads", "solar"]:
                                    metricsGroup = "."
                                else:
                                    metricsGroup = ".ha."
                                msg = metricsPrefix+metricsGroup+metric.replace(" ", "_")+" "+str(metrics[metric])+" "+str(int(time.time()))
                                debug("debugMetricsMsg", "sendMetrics", msg)
                                metricsSocket.send(bytes(msg+"\n", "utf-8"))
                except socket.error as exception:
                    log("sendMetrics", "socket error", str(exception))
                if metricsSocket:
                    debug("debugMetrics", "sendMetrics", "closing socket to", metricsHost)
                    metricsSocket.close()
        debug("debugMetrics", "sendMetrics", "metrics thread terminated")

    metricsThread = threading.Thread(target=sendMetricsThread)
    metricsThread.daemon = True
    metricsThread.start()
