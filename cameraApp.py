# Camera management
cameraPurge = False
cameraVideo = False
cameraSnaps = False
cameraMotion = False
cameraStorage = False

import sys
import time
import threading
from ha import *
from ha.camera.classes import *
from ha.camera.events import *
from ha.camera.video import *
from ha.camera.storage import *

if __name__ == "__main__":
    try:
        # running from command line
        today = sys.argv[1]
        force = True
        repeat = 0
        block = False
    except:
        # running as service
        today = time.strftime("%Y%m%d")
        force = False
        repeat = True
        block = True
    debug('debugEnable', "date:", today)
    debug('debugEnable', "force:", force)
    debug('debugEnable', "repeat:", repeat)
    debug('debugEnable', "block:", block)

    # get the camera attributes
    cameras = getCameras()

    # purge old video
    if cameraPurge:
        purgeThreads = []
        for cameraName in list(cameras.keys()):
            purgeThreads.append(LogThread(target=purgeStorage, args=(cameraName, repeat,)))
            purgeThreads[-1].start()

    # start the video threads
    if cameraVideo:
        videoThreads = []
        for camera in cameras:
            videoThreads.append(LogThread(target=recordVideo, args=(cameraDir, cameras[camera], today,)))
            videoThreads[-1].start()

    # start the snapshot threads
    if cameraSnaps:
        snapThreads = []
        delay = 0
        for camera in cameras:
            snapThreads.append(LogThread(target=snapshots, args=(cameraDir, cameras[camera], today, force, repeat, delay,)))
            snapThreads[-1].start()
            delay += 1

    # start the motion event threads
    if cameraMotion:
        motionEventThreads = []
        for camera in cameras:
            motionEventThreads.append(LogThread(target=motionEvents, args=(cameraDir, cameras[camera], today, force, repeat,)))
            motionEventThreads[-1].start()

    # start the event storage thread
    if cameraStorage:
        storageThread = LogThread(target=getStorageStats, args=(cameraDir, cameras, repeat,))
        storageThread.start()

    # block
    if block:
        while True:
            time.sleep(1)
