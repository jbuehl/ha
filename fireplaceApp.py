defaultConfig = {
    "video": "fireplace",
}

from ha import *
from ha.interfaces.fireplaceInterface import *
from ha.interfaces.fileInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()

    # Interfaces
    fileInterface = FileInterface("fileInterface", fileName=stateDir+"fireplace.state", event=stateChangeEvent, initialState=defaultConfig)
    fireplaceVideo = MultiControl("fireplaceVideo", fileInterface, "video", 
                                  values=["fireplace", "aquarium"],
                                  group="Fireplace", label="Fireplace video")
    fireplaceInterface = FireplaceInterface("fireplaceInterface", None, videoControl=fireplaceVideo)

    # controls
    fireplace = Control("fireplace", fireplaceInterface, type="fire", group="Fireplace", label="Fireplace")

    # Resources
    resources = Collection("resources", resources=[fireplace, fireplaceVideo,
                                                   ])
    restServer = RestServer("fireplace", resources, event=stateChangeEvent, label="Fireplace")

    # Start interfaces
    fileInterface.start()
    restServer.start()
