# basic camera functions
cameraBase = "/cameras/"

import json
from ha import *

cameraDir = cameraBase+"cameras/"
stateDir = cameraBase+"state/"
archiveDir = cameraBase+"archive/"

# directory structure:
    # <cameraBase>/
    #     state/
    #         storage.json                                        # storage stats
    #     cameras/
    #         <camera>/
    #            conf.json                                        # camera config
    #            videos/
    #                <YYYY>/
    #                    <MM>/
    #                        <DD>/
    #                             <YYYYMMDDHHMMSS>.ts             # video fragment
    #                             <YYYYMMDDHHMMSS>_record.m3u8    # recording playlist
    #                             <YYYYMMDDHHMMSS_event.m3u8      # event playlist
    #                             <YYYYMMDDHHMMSS_clip.m3u8       # clip playlist
    #            images/
    #                <YYYY>/
    #                    <MM>/
    #                        <DD>/
    #                             <YYYYMMDDHHMMSS>_motion.jpg     # motion event image
    #                             <YYYYMMDDHHMMSS>_door.jpg       # door event image
    #                             <YYYYMMDDHHMMSS>_doorbell.jpg   # doorbell event image
    #            snaps/
    #                <YYYY>/
    #                    <MM>/
    #                        <DD>/
    #                             <YYYYMMDDHHMMSS>_snap.jpg       # periodic snapshot thumbnail
    #     archive/
    #         <camera>/
    #            videos/
    #                <YYYY>/
    #                    <MM>/
    #                        <DD>/
    #                             <YYYYMMDDHHMMSS>.mp4            # archived video clip

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
        cameras[camera] = Camera(camera)
        try:
            cameras[camera].load(cameraDir+camera+"/conf.json")
            debug("debugCamera", "camera:", str(camera))
        except IOError:
            log("error reading config for camera", camera)
            del(cameras[camera])
    debug("debugCamera", "cameras:", str(cameras))
    return cameras

# create the camera directory path for a specific date
def dateDir(date):
    return date[0:4]+"/"+date[4:6]+"/"+date[6:8]+"/"
