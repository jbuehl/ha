# camera storage management
storageUpdateInterval = 60
purgeStorageInterval = 60*60*24 # daily
videoRetention = 10

import os
import time
import datetime
import subprocess
import json
from ha import *
from ha.camera.classes import *

# find the mount point of a directory
def mountPoint(path):
    path = os.path.realpath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path

# get the number of events and storage used
def getStorageStats(cameraDir, cameras, repeat):
    debug('debugEnable', "starting storage stats thread")
    repeating = True
    while repeating:
        todaysDatetime = datetime.datetime(*time.localtime()[0:6])
        startTimeDatetime = todaysDatetime - datetime.timedelta(days=videoRetention)
        eventStorage = {}
        for cameraName in sorted(list(cameras.keys())):
            debug('debugStorage', "getting eventStorage for camera", cameraName)
            dayDatetime = startTimeDatetime
            for day in range(videoRetention):
                updateStorageStats(cameraName, time.strftime("%Y%m%d", dayDatetime.timetuple()), cameraDir, eventStorage)
                dayDatetime += datetime.timedelta(days=1)
        debug('debugStorage', "eventStorage", eventStorage)
        makeDir(stateDir)
        json.dump(eventStorage, open(stateDir+"storage.json", "w"))
        debug('debugStorage', "saved storage stats")
        repeating = repeat
        time.sleep(storageUpdateInterval)

# return the number of events and video storage for the specified camera and day
def updateStorageStats(cameraName, day, cameraDir, eventStorage):
    videoBase = cameraDir+cameraName+"/videos/"
    imageBase = cameraDir+cameraName+"/images/"
    dayDir = day[0:4]+"/"+day[4:6]+"/"+day[6:8]
    nEvents = getEvents(imageBase+dayDir+"/")
    size = getSize(videoBase+dayDir+"/")
    eventStorage[cameraName+"/"+dayDir] = [nEvents, size]

# get number of events in the specified directory
def getEvents(path):
    try:
        eventFiles = os.listdir(path)
        return str(len(eventFiles))
    except OSError:
        return "0"

# get the sizes of the files in the specified directory
def getSize(path):
    try:
        fileSize = subprocess.check_output("du -h "+path, shell=True).decode()
        return fileSize.split("\t")[0]
    except subprocess.CalledProcessError:
        return "0"

# get the capacity, used, and free space on the specified device
def getStorage():
    device = mountPoint(cameraBase)
    storage = subprocess.check_output("df -h "+device, shell=True).decode().split("\n")[1].split()
    return storage[1:5]

# delete video older than the specified number of days
def purgeStorage(cameraName, repeat):
    repeating = True
    while repeating:
        debug('debugEnable', "deleting video older than", videoRetention, "days for camera", cameraName)
        if videoRetention > 0:
            osCommand("/usr/bin/find "+cameraDir+cameraName+"/videos"+" -mtime +"+str(videoRetention)+" -type f -delete")
            osCommand("/usr/bin/find "+cameraDir+cameraName+"/images"+" -mtime +"+str(videoRetention)+" -type f -delete")
            osCommand("/usr/bin/find "+cameraDir+cameraName+"/snaps"+" -mtime +"+str(videoRetention)+" -type f -delete")
            osCommand("/usr/bin/find "+cameraDir+cameraName+"/thumbs"+" -mtime +"+str(videoRetention)+" -type f -delete")
        repeating = repeat
        time.sleep(purgeStorageInterval)
