from ha.HAClasses import *
from ha.cameraInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    camera1 = CameraInterface("Camera1", imageDir="/root/", event=stateChangeEvent)
    
    # Cameras
    resources.addRes(HASensor("camera1", camera1, "image", group="Cameras", label="Camera 1", type="image"))
    resources.addRes(HASensor("camera1thumb", camera1, "thumb", group="Cameras", label="Camera 1 thumbnail", type="image"))
    resources.addRes(HAControl("camera1mode", camera1, "mode", group="Cameras", label="Camera 1 mode", type="cameraMode"))
    resources.addRes(HAControl("camera1enable", camera1, "enable", group="Cameras", label="Camera 1 enable", type="cameraEnable"))
    resources.addRes(HAControl("camera1record", camera1, "record", group="Cameras", label="Camera 1 record", type="cameraRecord"))
    
    # Schedules

    # Start interfaces
    camera1.start()
    restServer = RestServer(resources, event=stateChangeEvent)
    restServer.start()

