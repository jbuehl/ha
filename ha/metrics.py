
metricsPrefix = "com.example.ha"
metricsHost = "metrics.example.com"
metricsPort = 2003

import time
import socket
import threading
import json
import subprocess
import os
import socket
from ha import *

def startMetrics(resourceStates, sendMetrics=False, logMetrics=True, backupMetrics=True, purgeMetrics=False, purgeDays=5, logChanged=True):

    def sendMetricsThread():
        debug("debugMetrics", "sendMetrics", "metrics thread started")
        hostname = socket.gethostname()
        lastDay = ""
        changedStates = {}
        while True:
            # wait for a new set of states
            metrics = resourceStates.getStateChange()
            today = time.strftime("%Y%m%d")

            # log state deltas to a file
            if logMetrics:
                if today != lastDay:
                    lastStates = {}
                logFileName = logDir+today+".json"
                if logChanged:
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

            # copy to the backup server once per day
            if backupMetrics:
                if today != lastDay:
                    def backupMetricsThread():
                        debug("debugMetrics", "sendMetrics", "backup thread started")
                        try:
                            backupServer = subprocess.check_output("avahi-browse -atp|grep _backup|grep IPv4|cut -d';' -f4", shell=True).decode().split("\n")[0]+".local"
                            debug("debugMetrics", "backupMetrics", "backing up "+logDir+" to", backupServer)
                            os.popen("rsync -a "+logDir+"* "+backupServer+":/backups/ha/"+hostname+"/")
                        except Exception as ex:
                            log("metrics", "exception backing up metrics", str(ex))
                        debug("debugMetrics", "sendMetrics", "metrics thread ended")
                    backupThread = threading.Thread(target=backupMetricsThread)
                    backupThread.start()

            # purge metrics that have been backed up
            if purgeMetrics:
                if today != lastDay:
                    backupServer = subprocess.check_output("avahi-browse -atp|grep _backup|grep IPv4|cut -d';' -f4", shell=True).decode().split("\n")[0]+".local"
                    # get list of metrics files that are eligible to be purged
                    debug("debugPurgeMetrics", "purging metrics for", purgeDays, "days")
                    for metricsFile in sorted(os.listdir(logDir))[:-purgeDays]:
                        # only purge past files
                        debug("debugPurgeMetrics", "checking", metricsFile)
                        if metricsFile.split(".")[0] < today:
                            try:
                                # get sizes of the file and it's backup
                                fileSize = int(subprocess.check_output("ls -l "+logDir+metricsFile+"|cut -f5 -d' '", shell=True))
                                backupSize = int(subprocess.check_output("ssh "+backupServer+" ls -l /backups/ha/"+hostname+"/"+metricsFile+"|cut -f5 -d' '", shell=True))
                                if backupSize == fileSize:
                                    debug("debugPurgeMetrics", "deleting", metricsFile)
                                    os.popen("rm "+logDir+metricsFile)
                            except Exception as ex:
                                log("exception purging metrics file", metricsFile, str(ex))

            if today != lastDay:
                lastDay = today
        debug("debugMetrics", "sendMetrics", "metrics thread ended")

    metricsThread = threading.Thread(target=sendMetricsThread)
    metricsThread.start()
