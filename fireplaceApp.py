videoDir = "/video/"
defaultConfig = {
    "video": "fireplace",
}

import os
from ha import *
from ha.interfaces.videoInterface import *
from ha.interfaces.fileInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"fireplace.state", event=stateChangeEvent, initialState=defaultConfig)
    fireplaceVideo = MultiControl("fireplaceVideo", fileInterface, "video", values=sorted([video.split(".")[0] for video in os.listdir(videoDir)]),
                                  group="Fireplace", label="Fireplace video")
    fireplaceInterface = VideoInterface("fireplaceInterface", None, videoControl=fireplaceVideo)

    # controls
    fireplace = Control("fireplace", fireplaceInterface, type="fire", group="Fireplace", label="Fireplace")

    # Resources
    resources = Collection("resources", resources=[fireplace, fireplaceVideo,
                                                   ], event=stateChangeEvent)
    restServer = RestServer("fireplace", resources, event=stateChangeEvent, label="Fireplace")

    # Start interfaces
    fileInterface.start()
    restServer.start()
