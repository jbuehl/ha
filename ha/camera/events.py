# camera image functions
eventClipInterval = 30
snapshotInterval = 300
font = "Nimbus-Sans-L-Bold" # convert -list font

import subprocess
import os
import time
import datetime
from ha import *
from ha.camera.classes import *

width = 320
height = 180
convertCmd = """/usr/bin/convert %s -resize %dx%d \
-font %s -pointsize 18 \
-gravity southwest \
    -stroke '#000C' -strokewidth 4 -annotate 0 %s \
    -stroke  none   -fill white    -annotate 0 %s \
-gravity northwest \
    -stroke '#000C' -strokewidth 4 -annotate 0 %s \
    -stroke  none   -fill white    -annotate 0 %s \
%s
"""

def createEvent(eventType, camera, date, hour, minute, second="00"):
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
    videoDir = cameraDir+camera.name+"/videos/"+year+"/"+month+"/"+day+"/"
    thumbDir = cameraDir+camera.name+"/thumbs/"+year+"/"+month+"/"+day+"/"
    os.popen("mkdir -p "+thumbDir)
    try:
        videoFiles = os.listdir(videoDir)
        videoFiles.sort()
        # find the latest video fragment
        for videoFile in reversed(videoFiles):
            [videoName, ext] = videoFile.split(".")
            if ext == "ts":
                # wait for the fragment to finish recording
                time.sleep(10)
                debug("debugThumb", "creating", eventType, "event for camera", camera.name, "time", hour+":"+minute+":"+second)
                cmd = "ffmpeg -i "+videoDir+videoFile+" -vframes 1 -s 320x180 -nostats -loglevel error -y "+ \
                      thumbDir+videoName[0:8]+hour+minute+second+"_"+eventType.jpg"
                os.popen(cmd)
                break
    except OSError: # directory doesn't exist yet
        pass

# create thumbnail images for periodic snapshots
def snapshots(imageBase, camera, today, font, force=False, repeat=0):
    debug('debugEnable', "starting snapshot thread for camera", camera)
    lastMinute = "--"
    repeating = 1
    while repeating:
        # make a snapshot of the current video every 5 minutes
        hour = time.strftime("%H")
        minute = time.strftime("%M")
        if (minute[1] == "0") or (minute[1] == "5"):
            if minute != lastMinute:
                lastMinute = minute
                createEvent("snap", camera, today, hour, minute)
        repeating = repeat
        time.sleep(repeat)
    debug("debugThumb", "exiting snapshot thread for camera", camera.name)

# create thumbnail images for uploaded event images
def motionEvents(imageBase, camera, today, font, force=False, repeat=0):
    debug('debugEnable', "starting motion event thread for camera", camera)
    year = today[0:4]
    month = today[4:6]
    day = today[6:8]
    videoDir = imageBase+camera.name+"/videos/"+year+"/"+month+"/"+day+"/"
    imageDir = imageBase+camera.name+"/images/"+year+"/"+month+"/"+day+"/"
    thumbDir = imageBase+camera.name+"/thumbs/"+year+"/"+month+"/"+day+"/"
    snapDir = imageBase+camera.name+"/snaps/"+year+"/"+month+"/"+day+"/"
    os.popen("mkdir -p "+imageDir)
    os.popen("mkdir -p "+thumbDir)
    os.popen("mkdir -p "+snapDir)
    eventClipCount = eventClipInterval
    snapshotCount = snapshotInterval
    lastMinute = "--"
    repeating = 1
    while repeating:
        # make thumbnails for images
        if eventClipCount == eventClipInterval:
            eventClipCount = 0
            try:
                imageFiles = os.listdir(imageDir)
                imageFiles.sort()
                for imageFile in imageFiles:
                    [imageName, ext] = imageFile.split(".")
                    # select image files
                    if ext == "jpg":
                        # if the image file is not empty
                        if os.path.getsize(imageDir+imageFile) > 0:
                            # don't convert the image again unless the force flag is set
                            if force or (not os.path.exists(thumbDir+imageName+"_thumb.jpg")):
                                # time of event
                                event = imageName[-14:]
                                debug("debugThumb", "creating thumbnail for camera", camera.name, "event", event)
                                timeStamp = event[8:10]+":"+event[10:12]+":"+event[12:14]
                                # create the thumbnail image with timestamp text overlay
                                cmd = convertCmd % (imageDir+imageFile.replace(" ", "\ "), width, height,
                                                    font, timeStamp, timeStamp, "motion", "motion",
                                                    thumbDir+imageName.replace(" ", "\ ")+"_thumb.jpg")
                                os.popen(cmd)
            except OSError: # directory doesn't exist yet
                pass
        else:
            eventClipCount += 1
        repeating = repeat
        time.sleep(repeat)
    debug("debugThumb", "exiting motion event thread for camera", camera.name)
