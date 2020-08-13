
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

def startMetrics(resources, sendMetrics=False, logMetrics=True, backupMetrics=True, purgeMetrics=False, purgeDays=5, logChanged=True):

    def sendMetricsThread():
        debug("debugMetrics", "sendMetrics", "metrics thread started")
        hostname = socket.gethostname()
        lastDay = ""
        while True:
            # wait for a new set of states
            states = resources.getStates(wait=True)
            today = time.strftime("%Y%m%d")

            # log states to a file
            if logMetrics:
                if today != lastDay:    # start with a new baseline every day
                    lastStates = states
                changedStates = diffStates(lastStates, states, deleted=False)
                if changedStates != {}:
                    logFileName = logDir+today+".json"
                    debug("debugMetrics", "sendMetrics", "writing states to", logFileName)
                    with open(logFileName, "a") as logFile:
                        logFile.write(json.dumps([time.time(), (changedStates if logChanged else lastStates)])+"\n")
                lastStates = states

            # send states to the metrics server
            if sendMetrics:
                debug("debugMetrics", "sendMetrics", "opening socket to", metricsHost, metricsPort)
                try:
                    metricsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    metricsSocket.connect((metricsHost, metricsPort))
                    debug("debugMetrics", "sendMetrics", "sending", len(states), "metrics")
                    for state in list(states.keys()):
                        if state.split(".")[0] in ["loads", "solar"]:
                            metricsGroup = "."
                        else:
                            metricsGroup = ".ha."
                        msg = metricsPrefix+metricsGroup+state.replace(" ", "_")+" "+str(states[state])+" "+str(int(time.time()))
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
                            pid = subprocess.Popen("rsync -a "+logDir+"* "+backupServer+":/backups/ha/"+hostname+"/", shell=True)
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
                    debug("debugPurgeMetrics", "purging metrics more than", purgeDays, "days old")
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
                                    os.remove(logDir+metricsFile)
                            except Exception as ex:
                                log("exception purging metrics file", metricsFile, str(ex))

            if today != lastDay:
                lastDay = today
        debug("debugMetrics", "sendMetrics", "metrics thread ended")

    metricsThread = threading.Thread(target=sendMetricsThread)
    metricsThread.start()
