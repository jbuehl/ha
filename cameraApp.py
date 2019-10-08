# Camera management

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
        purge = False
        video = False
        storage = False
        block = False
    except:
        # running as service
        today = time.strftime("%Y%m%d")
        force = False
        repeat = True
        purge = True
        video = True
        storage = True
        block = True
    debug('debugEnable', "date:", today)
    debug('debugEnable', "force:", force)
    debug('debugEnable', "repeat:", repeat)
    debug('debugEnable', "purge:", purge)
    debug('debugEnable', "video:", video)
    debug('debugEnable', "storage:", storage)
    debug('debugEnable', "block:", block)

    # get the camera attributes
    cameras = getCameras()

    # purge old video
    if purge:
        purgeThreads = []
        for camera in list(cameras.keys()):
            purgeThreads.append(threading.Thread(target=purgeStorage, args=(camera, repeat,)))
            purgeThreads[-1].daemon = True
            purgeThreads[-1].start()

    # start the video threads
    if video:
        videoThreads = []
        for camera in cameras:
            videoThreads.append(threading.Thread(target=recordVideo, args=(cameraDir, cameras[camera], today,)))
            videoThreads[-1].daemon = True
            videoThreads[-1].start()

    # start the snapshot threads
    snapThreads = []
    for camera in cameras:
        snapThreads.append(threading.Thread(target=snapshots, args=(cameraDir, cameras[camera], today, force, repeat,)))
        snapThreads[-1].daemon = True
        snapThreads[-1].start()

    # start the motion event threads
    motionEventThreads = []
    for camera in cameras:
        motionEventThreads.append(threading.Thread(target=motionEvents, args=(cameraDir, cameras[camera], today, force, repeat,)))
        motionEventThreads[-1].daemon = True
        motionEventThreads[-1].start()

    # start the event storage thread
    if storage:
        storageThread = threading.Thread(target=getStorageStats, args=(cameraDir, cameras, repeat,))
        storageThread.daemon = True
        storageThread.start()

    # block
    if block:
        while True:
            time.sleep(1)
