# Camera interface

# Functions:
#    get/set attributes
#    enable/disable camera
#    take picture
#    start/stop video
#    start/stop motion detection
#    get image
#    get video

# Controls:
#    image
#    mode
#    enable
#    resolution
#    rate
#    rotation
#    thumb

# Modes:
modeStill = 0
modeYime = 1
modeVideo = 2
modeMotion = 3

import subprocess
import threading
from ha import *

class CameraInterface(Interface):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface=None, event=None, mode=modeStill, imageDir="", rotation=0, enabled=True):
        Interface.__init__(self, name, interface=interface, event=event)
        self.mode = mode
        self.imageFileName = imageDir+self.name
        self.rotation = rotation
        self.enabled = enabled
        self.recording = False

    def read(self, addr):
        debug('debugCamera', self.name, "read", addr)
        if addr == "mode":
            return self.getMode()
        if addr == "enable":
            return self.getEnable()
        if addr == "record":
            return self.getRecording()
        elif addr == "image":
            if self.mode == modeStill:
                return self.getImage()
            elif self.mode == modeVideo:
                return self.getVideo()
        elif addr == "thumb":
            return self.getThumb()

    def write(self, addr, value):
        debug('debugCamera', self.name, "write", addr, value)
        if addr == "mode":
            self.setMode(value)
        elif addr == "enable":
            self.setEnable(value)
        elif addr == "record":
            self.setRecording(value)

    def getStateType(self, sensor):
        if (sensor.addr == "image") or (sensor.addr == "thumb"):
            return dict
        else:
            return int
        
    # Get the mode of the camera
    def getMode(self):
        debug('debugCamera', self.name, "getMode ")
        return self.mode

    # Set the mode of the camera
    def setMode(self, value):
        debug('debugCamera', self.name, "setMode", value)
        self.mode = value
        self.notify()

    # Enable/disable the camera
    def getEnable(self):
        debug('debugCamera', self.name, "getEnable")
        return self.enabled

    # Enable/disable the camera
    def setEnable(self, value):
        debug('debugCamera', self.name, "setEnable", value)
        self.enabled = value
        self.notify()

    # Return recording state of the camera
    def getRecording(self):
        debug('debugCamera', self.name, "getRecording")
        return self.recording

    # record an image or video
    def setRecording(self, value):
        debug('debugCamera', self.name, "setRecording", value)
        if self.mode == modeStill:
            if value == 1:  # take a picture
                self.recording = True
                self.notify()
                self.takePicture()
            else:
                self.recording = False            
                self.notify()
        elif self.mode == "time":
            if state == 1:  # start the sampling
                self.recording = True
            else:           # stop the sampling
                self.recording = False
#        elif self.mode == "video":
#            if state == 1:  # start the video
#            else:           # stop the video
#        elif self.mode == "motion":
#            if state == 1:  # start the motion detection
#            else:           # stop the motion detection

    def takePicture(self):
        def takePicture():
#            try:
            subprocess.check_output("/opt/vc/bin/raspistill -rot %d -o %s.jpg"%(self.rotation, self.imageFileName), shell=True)
            subprocess.check_output("/usr/bin/convert %s.jpg -resize 120x90 %s-thumb.jpg"%(self.imageFileName, self.imageFileName), shell=True)
#            except:
#                pass
            self.recording = False
            self.notify()
        takePictureThread = threading.Thread(target=takePicture)
        takePictureThread.start()
            
    # return the current image
    def getImage(self):
        debug('debugCamera', self.name, "getImage")
        with open(self.imageFileName+".jpg") as imageFile:
            image = imageFile.read()
        debug('debugCamera', self.name, len(image), "bytes read")
        return {"contentType": "image/jpeg", "data": image}

    # return the video stream
    def getVideo(self):
        debug('debugCamera', self.name, "getVideo")

    # return the thumbnail
    def getThumb(self):
        debug('debugCamera', self.name, "getThumb")
        with open(self.imageFileName+"-thumb.jpg") as imageFile:
            image = imageFile.read()
        debug('debugCamera', self.name, len(image), "bytes read")
        return {"contentType": "image/jpeg", "data": image}

