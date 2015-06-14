import socket
from ha.HAClasses import *
from ha.cameraInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Environment
    cameraName = socket.gethostname()
    cameraDisplay = cameraName[:-1].capitalize()+" "+cameraName[-1]

    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    camera = CameraInterface(cameraName, imageDir="/root/", rotation=cameraRotation, event=stateChangeEvent)
    
    # Cameras
    resources.addRes(HASensor(cameraName+"image", camera, "image", group="Cameras", label=cameraDisplay, type="image"))
    resources.addRes(HASensor(cameraName+"thumb", camera, "thumb", group="Cameras", label=cameraDisplay+" thumbnail", type="image"))
    resources.addRes(HAControl(cameraName+"mode", camera, "mode", group="Cameras", label=cameraDisplay+" mode", type="cameraMode"))
    resources.addRes(HAControl(cameraName+"enable", camera, "enable", group="Cameras", label=cameraDisplay+" enable", type="cameraEnable"))
    resources.addRes(HAControl(cameraName+"record", camera, "record", group="Cameras", label=cameraDisplay+" record", type="cameraRecord"))
    
    # Schedules

    # Start interfaces
    camera.start()
    restServer = RestServer(resources, event=stateChangeEvent, label=cameraDisplay)
    restServer.start()

