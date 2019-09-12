# basic camera functions
cameraBase = "/cameras/"
cameraDir = cameraBase+"cameras/"

import json
from ha import *

# directory structure:
#    base
#        camera
#            videos
#                year
#                    month
#                        day
#            images
#                year
#                    month
#                        day
#            thumbs
#                year
#                    month
#                        day
#            snaps
#                year
#                    month
#                        day

class Camera(object):
    def __init__(self, name, label=None, ipAddr=""):
        self.name = name
        if label:
            self.label = label
        else:
            self.label = name
        self.ipAddr = ipAddr

    def load(self, loadFileName):
        with open(loadFileName) as loadFile:
            attrs = json.load(loadFile)
        for attr in attrs.keys():
            setattr(self, attr, attrs[attr])

# get the camera attributes
def getCameras():
    cameraList = None
    while not cameraList:
        try:
            cameraList = os.listdir(cameraDir)
        except OSError:
            log("camera storage", cameraDir, "not available")
            time.sleep(1)
    cameras = {}
    for camera in cameraList:
        if camera != "storage.json":
            cameras[camera] = Camera(camera)
            try:
                cameras[camera].load(cameraDir+camera+"/conf.json")
                debug("debugCamera", "camera:", str(camera))
            except:
                raise
    debug("debugCamera", "cameras:", str(cameras))
    return cameras
