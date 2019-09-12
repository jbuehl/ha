# Camera management

import sys
import time
import threading
from ha import *
from ha.camera.classes import *
from ha.camera.images import *
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
    except:
        # running as service
        today = time.strftime("%Y%m%d")
        force = False
        repeat = True
        purge = True
        video = True
        storage = True
    debug('debugEnable', "date:", today)
    debug('debugEnable', "force:", force)
    debug('debugEnable', "repeat:", repeat)
    debug('debugEnable', "purge:", purge)
    debug('debugEnable', "video:", video)
    debug('debugEnable', "storage:", storage)

    # get the camera attributes
    cameras = getCameras()

    # purge old video
    if purge:
        purgeThreads = []
        for camera in cameras.keys():
            purgeThreads.append(threading.Thread(target=purgeStorage, args=(camera, repeat,)))
            purgeThreads[-1].start()

    # start the video threads
    if video:
        videoThreads = []
        for camera in cameras:
            videoThreads.append(threading.Thread(target=recordVideo, args=(cameraBase, cameras[camera], today,)))
            videoThreads[-1].start()

    # start the thumbnail threads
    thumbThreads = []
    for camera in cameras:
        thumbThreads.append(threading.Thread(target=thumbNails, args=(cameraBase, cameras[camera], today, font, force, repeat,)))
        thumbThreads[-1].start()

    # start the event playlist threads
    eventThreads = []
    for camera in cameras:
        eventThreads.append(threading.Thread(target=makeEventPlaylists, args=(cameraBase, cameras[camera], today, force, repeat,)))
        eventThreads[-1].start()

    # start the event storage thread
    storageThread = threading.Thread(target=getStorageStats, args=(cameraBase, cameras, repeat,))
    storageThread.start()

    # block
    while True:
        time.sleep(1)
