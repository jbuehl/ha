# Camera interface

# Functions:
#    get/set attributes
#    enable/disable camera
#    take picture
#    start/stop video
#    start/stop motion detection
#    get image
#    get video

# Modes:
#    image
#    video
#    motion

import subprocess
from ha.HAClasses import *

class CameraInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        debug('debugCamera', self.name, "read", addr)
        return 1

    def write(self, addr, value):
        debug('debugCamera', self.name, "write", addr, value)

class Camera(HAControl):
    def __init__(self, name, interface, mode="image", addr=None, group="", type="camera", location=None, view=None, label="", interrupt=None, event=None):
        HAControl.__init__(self, name, interface, addr, group=group, type=type, location=location, view=view, label=label, interrupt=interrupt, event=event)
        self.mode = mode
        self.imageFileName = "/root/test.jpg"
        self.__dict__["image"] = None   # dummy class variable so hasattr() returns True
        self.__dict__["video"] = None   # dummy class variable so hasattr() returns True
        self.attrTypes = {"image": "image/jpeg"}

    # Set the mode of the camera
    def setMode(self, mode):
        debug('debugCamera', self.name, "setMode ", mode)
        self.mode = mode
        return True

    # return the current image
    def getImage(self):
        debug('debugCamera', self.name, "getImage")
#        try:
        subprocess.check_output("/opt/vc/bin/raspistill -v -o %s"%(self.imageFileName),shell=True)
        with open(self.imageFileName) as imageFile:
            image = imageFile.read()
#        except:
#            image = ""
        return image

    # return the video stream
    def getVideo(self):
        debug('debugCamera', self.name, "getVideo")
        try:
            subprocess.check_output("/opt/vc/bin/raspistill -v -o %s"%(self.imageFileName),shell=True)
            with open(self.imageFileName) as imageFile:
                return imageFile.read()
        except:
            return ""

    # override to handle special cases of image and video
    def __getattribute__(self, attr):
        if attr == "image":
            return self.getImage()
        elif attr == "video":
            return self.getVideo()
        else:
            return HAControl.__getattribute__(self, attr)
            
    # dictionary of pertinent attributes
    def dict(self):
        return HAControl.dict(self)#.update({"mode":self.mode})

