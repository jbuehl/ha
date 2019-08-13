#!/usr/bin/python

# Read a file that contains logging data from electrical power load current sensors.
# Compute statistics and send to graphing server.

# Usage: statsApp [-f] inFile
# Arguments:
#   inFile        log file or directory to read
#                   If a file is specified, the program processes the data in that file and
#                   terminates, unless the -f option is specified, in which case it waits for
#                   further data to be written to the input file.
#                   If a directory is specified, all files in the directory are processed.
#                   If a directory is specified and the -f option is specified, only the file
#                   in the directory with the newest modified date is processed and the program
#                   waits for further data in that file.  If a new file is subsequently created in
#                   the directory, the current file is closed and the new file is opened.
# Options:
#   -f              follow as the input file grows (as in tail -f)

# configuration
inFileName = ""
fileDate = ""
follow = False
readInterval = .1

# file handles
inFile = None

# graphite
graphiteSocket = None
metricsPrefix = ""
metricsHost = ""
port = 2003

import os
import socket
import struct
import sys
import time
import getopt
import syslog
import datetime
import json
from ha import *

lastTime = 0
lastTimeLog = 0
stateDict = {
    "loads.ac.power": 0.0,
    "loads.appliance1.power": 0.0,
    "loads.appliance2.power": 0.0,
    "loads.backhouse.power": 0.0,
    "loads.carcharger.power": 0.0,
    "loads.cooking.power": 0.0,
    "loads.lights.power": 0.0,
    "loads.plugs.power": 0.0,
    "loads.pool.power": 0.0,
    "loads.ac.power": 0.0,
    "loads.appliance1.dailyEnergy": 0.0,
    "loads.appliance2.dailyEnergy": 0.0,
    "loads.backhouse.dailyEnergy": 0.0,
    "loads.carcharger.dailyEnergy": 0.0,
    "loads.cooking.dailyEnergy": 0.0,
    "loads.lights.dailyEnergy": 0.0,
    "loads.plugs.dailyEnergy": 0.0,
    "loads.pool.dailyEnergy": 0.0,
    "loads.stats.power": 0.0,
    "loads.stats.dailyEnergy": 0.0,
}

# get command line options and arguments
def getOpts():
    global follow
    global inDir, inFileName, inFiles
    (opts, args) = getopt.getopt(sys.argv[1:], "f")
    try:
        inFileName = args[0]
        if os.path.isdir(inFileName): # a directory was specified
            inDir = inFileName.rstrip("/")+"/"
            inFiles = os.listdir(inDir)
        else:                           # a file was specified
            inDir = ""
            inFiles = [inFileName]
    except:
        terminate(1, "input file must be specified")
    for opt in opts:
        if opt[0] == "-f":
            follow = True
    debug("debugStats", "inFileName:", inFileName)
    debug("debugStats", "follow:", follow)

# open the specified input file
def openInFile(inFileName):
    global inFile, fileDate
    if inFileName == "stdin":
        inFile = sys.stdin
    else:
        try:
            debug("debugStats",  inFileName)
            inFile = open(inFileName)
            fileDate = inFileName.split(".")[0].split("-")[-1]
            fileDate = fileDate[0:4]+"-"+fileDate[4:6]+"-"+fileDate[6:8]
        except:
            terminate(1, "Unable to open "+inFileName)

# close the currently open input file
def closeInFile(inFile):
    if inFile:
        debug("debugStats", "closing", inFileName)
        inFile.close()

# open the last modified file in the in directory
def openLastinFile():
    global inFileName, inDir, inFile
    if inDir != "":   # directory was specified
        try:
            inFiles = os.listdir(inDir)
        except:
            terminate(1, "Unable to access directory "+inDir)
        latestModTime = 0
        # find the name of the file with the largest modified time
        for fileName in inFiles:
            inModTime = os.path.getmtime(inDir+fileName)
            if inModTime > latestModTime:
               latestModTime = inModTime
               latestFileName = inDir+fileName
        if inFileName != latestFileName:  # is there a new file?
            closeInFile(inFile)
            inFileName = latestFileName
            openInFile(inFileName)
            zeroDaily()
    else:   # just open the specified file the first time this is called
        if not inFile:
            openInFile(inFileName)

# close all files
def closeFiles():
    if inFile: inFile.close()

def terminate(code, msg=""):
    log("terminating", msg)
    sys.exit(code)

# zero the daily totals
def zeroDaily():
    global stateDict
    for item in stateDict.keys():
        itemParts = item.split(".")
        if itemParts[2] == "dailyEnergy":
            stateDict[item] = 0.0

# parse input power readings
def parseInput(inRec):
    global lastTime, lastTimeLog, stateDict
    try:
        [timeStamp, inDict] = json.loads(inRec)
        timeStamp = int(timeStamp)
        # if timeStamp < 1561332200: return
        # periodically log the time that is being processed
        if timeStamp > lastTimeLog+3600:
            log("processing", time.asctime(time.localtime(timeStamp)))
            lastTimeLog = timeStamp
        if lastTime == 0:
            lastTime = timeStamp
        timeDiff = timeStamp - lastTime
        debug("debugStats", "input:", timeStamp, inDict)
        # compute energy consumed since last measurement
        stateDict["loads.stats.power"] = 0.0
        for item in stateDict.keys():
            itemParts = item.split(".")
            if itemParts[0] == "loads":
                if itemParts[1] != "stats":
                    if itemParts[2] == "power":
                        # add to the total power for this period
                        stateDict["loads.stats.power"] += stateDict[item]
                        # calculate energy consumed since last measurement for this sensor
                        energy = stateDict[item] * timeDiff / 3600
                        try:
                            stateDict["loads."+itemParts[1]+".dailyEnergy"] += energy
                            stateDict["loads.stats.dailyEnergy"] += energy
                        except KeyError:
                            stateDict["loads."+itemParts[1]+".dailyEnergy"] = 0.0
                        debug("debugStats", "energy:", item, stateDict[item], energy, stateDict["loads."+itemParts[1]+".dailyEnergy"])
        # update the measurements
        for item in inDict.keys():
            itemParts = item.split(".")
            if itemParts[0] == "loads":
                if itemParts[1] != "stats":
                    if inDict[item] == None:
                        inDict[item] = 0.0
                    stateDict[item] = inDict[item]
                debug("debugStats", "power: ", item, inDict[item])
        debug("debugStats", "state:", stateDict)
        lastTime = timeStamp
    except Exception as ex:
        log("exception", str(ex), inRec[0:40])

def writeGraphite(timeStamp):
    try:
        metricsSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        metricsSocket.connect((metricsHost, port))
        for item in stateDict.keys():
            metric = "%s.%s %s %d" % (metricsPrefix, item, str(stateDict[item]), timeStamp)
            debug("debugStats", "metric:", metric)
            metricsSocket.send(metric+"\n")
    except socket.error as exception:
        log("sendMetrics", "socket error", str(exception))
    if metricsSocket:
        metricsSocket.close()
    return

if __name__ == "__main__":
    getOpts()
    graphiteSocket = True # openGraphite(hostName, port)
    # process the input file(s)
    if follow:      # following - start
        # open the latest input file in the in directory
        openLastinFile()
        while True: # read forever
            inRec = inFile.readline()
            if inRec:
                # sometimes readline doesn't get everything
                # if the read didn't get the whole line, read more
                while inRec[-1] != "\n":
                    time.sleep(readInterval)
                    debug("debugStats", "read again")
                    inRec += inFile.readline()
                parseInput(inRec)
                writeGraphite(lastTime)
            else:   # end of file - see if a new file has been opened before trying again
                openLastinFile()
            time.sleep(readInterval)
    else:       # not following - process whatever files were specified and exit
        for inFileName in inFiles:
            debug("debugStats", "reading:", inDir+inFileName)
            openInFile(inDir+inFileName)
            inRec = inFile.readline()
            while inRec:
                parseInput(inRec)
                writeGraphite(lastTime)
                inRec = inFile.readline()
            closeInFile(inFile)
        closeFiles()
        terminate(0, "Done")
