# camera image functions
eventClipInterval = 30
thumbWidth = 320
thumbHeight = 180
# font = "Nimbus-Sans-L-Bold" # convert -list font

import subprocess
import os
import time
import datetime
from ha import *
from ha.camera.classes import *
from ha.camera.video import *

# convertCmd = """/usr/bin/convert %s -resize %dx%d \
# -font %s -pointsize 18 \
# -gravity southwest \
#     -stroke '#000C' -strokewidth 4 -annotate 0 %s \
#     -stroke  none   -fill white    -annotate 0 %s \
# -gravity northwest \
#     -stroke '#000C' -strokewidth 4 -annotate 0 %s \
#     -stroke  none   -fill white    -annotate 0 %s \
# %s
# """
convertCmd = """/usr/bin/convert %s -resize %dx%d \
%s
"""

def createEvent(eventType, cameraName, date, hour, minute, second="00"):
    videoDir = cameraDir+cameraName+"/videos/"+dateDir(date)
    thumbDir = cameraDir+cameraName+"/thumbs/"+dateDir(date)
    os.popen("mkdir -p "+thumbDir)
    try:
        (tsFiles, firstFile) = findChunk(videoDir, hour+minute+second)
        # wait for the fragment to finish recording
        time.sleep(10)
        debug("debugThumb", "creating", eventType, "event for camera", cameraName, "at", hour+":"+minute+":"+second)
        cmd = "ffmpeg -i "+videoDir+tsFiles[firstFile]+" -vframes 1 -s "+str(thumbWidth)+"x"+str(thumbHeight)+" -nostats -loglevel error -y "+ \
              thumbDir+date+hour+minute+second+"_"+eventType+".jpg"
        os.popen(cmd)
    except OSError: # directory doesn't exist yet
        pass

# create thumbnail images for periodic snapshots
def snapshots(imageBase, camera, date, force=False, repeat=0):
    debug('debugEnable', "starting snapshot thread for camera", camera.name)
    lastMinute = "--"
    repeating = 1
    while repeating:
        # make a snapshot of the current video every 5 minutes
        hour = time.strftime("%H")
        minute = time.strftime("%M")
        if (minute[1] == "0") or (minute[1] == "5"):
            if minute != lastMinute:
                lastMinute = minute
                createEvent("snap", camera.name, date, hour, minute)
        repeating = repeat
        time.sleep(repeat)
    debug("debugThumb", "exiting snapshot thread for camera", camera.name)

# create thumbnail images for event images uploaded from cameras
def motionEvents(imageBase, camera, date, force=False, repeat=0):
    debug('debugEnable', "starting motion event thread for camera", camera.name)
    videoDir = imageBase+camera.name+"/videos/"+dateDir(date)
    imageDir = imageBase+camera.name+"/images/"+dateDir(date)
    thumbDir = imageBase+camera.name+"/thumbs/"+dateDir(date)
    os.popen("mkdir -p "+imageDir)
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
                    # rename to get rid of the stuff prefixing the timestamp
                    newImageFile = imageFile.split("_")[-1]
                    if newImageFile != imageFile:
                        debug("debugThumb", "renaming ", imageDir+imageFile, "to", imageDir+newImageFile)
                        os.popen("mv "+imageDir+imageFile.replace(" ", "\ ")+" "+imageDir+newImageFile)
                        imageFile = newImageFile
                    [imageName, ext] = imageFile.split(".")
                    # if the image file is not empty
                    if os.path.getsize(imageDir+imageFile) > 0:
                        # don't convert the image again unless the force flag is set
                        if force or (not os.path.exists(thumbDir+imageName+"_motion.jpg")):
                            # time of event
                            event = imageName[-14:]
                            debug("debugThumb", "creating thumbnail for camera", camera.name, "event", event)
                            timeStamp = event[8:10]+":"+event[10:12]+":"+event[12:14]
                            # create the thumbnail image with timestamp text overlay
                            cmd = convertCmd % (imageDir+imageFile, thumbWidth, thumbHeight,
                                                # font, timeStamp, timeStamp, "motion", "motion",
                                                thumbDir+imageName+"_motion.jpg")
                            os.popen(cmd)
            except OSError: # directory doesn't exist yet
                pass
        else:
            eventClipCount += 1
        repeating = repeat
        time.sleep(repeat)
    debug("debugThumb", "exiting motion event thread for camera", camera.name)
