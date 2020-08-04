videoDir = "/video/"
defaultConfig = {
    "video": "pumpkin",
}

import os
from ha import *
from ha.interfaces.videoInterface import *
from ha.interfaces.fileInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"halloween.state", event=stateChangeEvent, initialState=defaultConfig)
    halloweenVideo = MultiControl("halloweenVideo", fileInterface, "video", values=sorted([video.split(".")[0] for video in os.listdir(videoDir)]),
                                  group=["Holiday", "Halloween"], label="Halloween video")
    videoInterface = VideoInterface("videoInterface", None, videoControl=halloweenVideo)

    # controls
    halloween = Control("halloween", videoInterface, group=["Holiday", "Halloween"], label="Halloween")

    # Resources
    resources = Collection("resources", resources=[halloween, halloweenVideo,
                                                   ], event=stateChangeEvent)
    restServer = RestServer("halloween", resources, event=stateChangeEvent, label="Halloween")

    # Start interfaces
    fileInterface.start()
    restServer.start()
