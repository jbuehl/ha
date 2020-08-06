# basic camera functions
cameraBase = "/cameras/"

import json
import os
from ha import *

cameraDir = cameraBase+"cameras/"
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
        for attr in list(attrs.keys()):
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

# split a timestamp YYYYMMDDHHMMSS into YYYYMMDD, HH, MM, SS
def splitTime(timeStamp):
    # truncate or extend with 0 if short
    ts = timeStamp[0:14]+"0"*(14-len(timeStamp))
    return [ts[0:8], ts[8:10], ts[10:12], ts[12:14]]

# add two times represented by a string of the form HHMMSS
# assume result is in the same day
def addTimes(time1, time2):
    [hh1, mm1, ss1] = [int(time1[0:2]), int(time1[2:4]), int(time1[4:6])]
    [hh2, mm2, ss2] = [int(time2[0:2]), int(time2[2:4]), int(time2[4:6])]
    t1 = hh1 * 3600 + mm1 * 60 + ss1
    t2 = hh2 * 3600 + mm2 * 60 + ss2
    hh = int((t1 + t2) / 3600)
    mm = int(((t1 + t2) % 3600) / 60)
    ss = int(((t1 + t2) % 3600) % 60)
    return "%02d%02d%02d"%(hh, mm, ss)

# subtract two times represented by a string of the form HHMMSS
# assume result is in the same day
def subTimes(time1, time2):
    [hh1, mm1, ss1] = [int(time1[0:2]), int(time1[2:4]), int(time1[4:6])]
    [hh2, mm2, ss2] = [int(time2[0:2]), int(time2[2:4]), int(time2[4:6])]
    t1 = hh1 * 3600 + mm1 * 60 + ss1
    t2 = hh2 * 3600 + mm2 * 60 + ss2
    hh = int((t1 - t2) / 3600)
    mm = int(((t1 - t2) % 3600) / 60)
    ss = int(((t1 - t2) % 3600) % 60)
    return "%02d%02d%02d"%(hh, mm, ss)

# create a directory and any parent directories necessary
# don't raise an exception if the directory already exists
def makeDir(path):
    try:
        os.makedirs(path)
    except FileExistsError:
        pass
