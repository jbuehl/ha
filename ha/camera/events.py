# camera image functions

eventClipInterval = 30
snapWidth = 320
snapHeight = 180

import subprocess
import os
import time
import datetime
from ha import *
from ha.camera.classes import *
from ha.camera.video import *

# find the offset into a video fragment for the specified time
def findOffset(tsFile, hour, minute, second):
    tsTime = tsFile.split(".")[0]
    offset = (int(hour)*3600 + int(minute)*60 + int(second)) - (int(tsTime[8:10])*3600 + int(tsTime[10:12])*60 + int(tsTime[12:14]))
    debug("debugThumb", "tsTime", tsTime, hour+minute+second, "offset", offset)
    return offset

def createEvent(eventType, cameraName, eventTime):
    [date, hour, minute, second] = splitTime(eventTime)
    videoDir = cameraDir+cameraName+"/videos/"+dateDir(date)
    imageDir = cameraDir+cameraName+"/images/"+dateDir(date)
    os.popen("mkdir -p "+imageDir)
    os.popen("chown -R "+ftpUsername+"."+ftpUsername+" "+cameraDir+cameraName+"/images/")
    try:
        (tsFiles, firstFile) = findChunk(videoDir, hour+minute+second)
        # wait for the fragment to finish recording
        time.sleep(10)
        offset = 0 # findOffset(tsFiles[firstFile], hour, minute, second)
        if offset >= 0:
            debug("debugThumb", "creating", eventType, "event for camera", cameraName, "at", hour+minute+second, "from", tsFiles[firstFile], "offset", offset)
            cmd = "/usr/bin/ffmpeg -ss 0:%02d"%(offset)+" -i "+videoDir+tsFiles[firstFile]+" -vframes 1 -nostats -loglevel error -y "+ \
                  imageDir+date+hour+minute+second+"_"+eventType+".jpg"
            os.popen(cmd)
    except (OSError, IndexError) as ex: # directory doesn't exist yet
        log("createEvent", "exception", str(ex))

def createSnap(cameraName, eventTime, wait=True):
    [date, hour, minute, second] = splitTime(eventTime)
    # debug("debugSnaps", "createSnap", cameraName, date, hour, minute, second, wait)
    videoDir = cameraDir+cameraName+"/videos/"+dateDir(date)
    thumbDir = cameraDir+cameraName+"/thumbs/"+dateDir(date)
    os.popen("mkdir -p "+thumbDir)
    try:
        (tsFiles, firstFile) = findChunk(videoDir, hour+minute+second)
        # debug("debugSnaps", "createSnap", cameraName, firstFile, tsFiles[firstFile])
        if wait:
            # wait for the fragment to finish recording
            time.sleep(10)
        offset = 0 # findOffset(tsFiles[firstFile], hour, minute, second)
        if offset >= 0:
            debug("debugSnaps", "creating snapshot for camera", cameraName, "at", hour+minute+second, "from", tsFiles[firstFile], "offset", offset)
            cmd = "/usr/bin/ffmpeg -ss 0:%02d"%(offset)+" -i "+videoDir+tsFiles[firstFile]+" -vframes 1 -s "+str(snapWidth)+"x"+str(snapHeight)+ \
                  " -nostats -loglevel error -y "+ \
                  thumbDir+date+hour+minute+second+"_snap.jpg"
            os.popen(cmd)
    except (OSError, IndexError) as ex: # directory or video file doesn't exist yet
        log("createSnap", "exception", str(ex))

# create thumbnail images for periodic snapshots
def snapshots(imageBase, camera, date, force=False, repeat=0):
    debug('debugEnable', "starting snapshot thread for camera", camera.name)
    # create snapshots starting at the current time
    lastSecond = "--"
    repeating = 1
    time.sleep(10)  # wait until there is at least one video file
    while repeating:
        # make a snapshot of the current video every 10 seconds
        now = time.strftime("%H%M%S")
        second = now[4:6]
        if second[1] == "0":
            if second != lastSecond:
                lastSecond = second
                # create a snapshot for the time 10 seconds ago
                createSnap(camera.name, date+subTimes(now, "000010"), False)
        repeating = repeat
        time.sleep(repeat)
    debug("debugEnable", "ending snapshot thread for camera", camera.name)

# create thumbnail images for event images uploaded from cameras
def motionEvents(imageBase, camera, date, force=False, repeat=0):
    debug('debugEnable', "starting motion event thread for camera", camera.name)
    videoDir = imageBase+camera.name+"/videos/"+dateDir(date)
    imageDir = imageBase+camera.name+"/images/"+dateDir(date)
    thumbDir = imageBase+camera.name+"/thumbs/"+dateDir(date)
    os.popen("mkdir -p "+imageDir)
    os.popen("chown -R "+ftpUsername+"."+ftpUsername+" "+cameraDir+camera.name+"/images/")
    os.popen("mkdir -p "+thumbDir)
    eventClipCount = eventClipInterval
    repeating = 1
    while repeating:
        # make thumbnails for images
        if eventClipCount == eventClipInterval:
            eventClipCount = 0
            try:
                imageFiles = os.listdir(imageDir)
                imageFiles.sort()
                for imageFile in imageFiles:
                    # rename to get rid of the stuff prefixing the timestamp that the camera creates
                    [imageName, ext] = imageFile.split(".")
                    imageNameParts = imageName.split("_")
                    if imageNameParts[-1].isdigit():
                        newImageFile = imageNameParts[-1]+"_motion.jpg"
                        debug("debugThumb", "renaming ", imageDir+imageFile, "to", imageDir+newImageFile)
                        os.popen("mv "+imageDir+imageFile.replace(" ", "\ ")+" "+imageDir+newImageFile)
            except OSError: # directory doesn't exist yet
                pass
        else:
            eventClipCount += 1
        repeating = repeat
        time.sleep(repeat)
    debug("debugEnable", "ending motion event thread for camera", camera.name)
