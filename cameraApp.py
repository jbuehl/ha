import socket
from ha import *
from ha.interfaces.cameraInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    # Environment
    cameraName = socket.gethostname()
    cameraDisplay = cameraName[:-1].capitalize()+" "+cameraName[-1]

    # Resources
    resources = Collection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    camera = CameraInterface(cameraName, imageDir="/root/", rotation=cameraRotation, event=stateChangeEvent)
    
    # Cameras
    resources.addRes(Sensor(cameraName+"image", camera, "image", group="Cameras", label=cameraDisplay, type="image"))
    resources.addRes(Sensor(cameraName+"thumb", camera, "thumb", group="Cameras", label=cameraDisplay+" thumbnail", type="image"))
    resources.addRes(Control(cameraName+"mode", camera, "mode", group="Cameras", label=cameraDisplay+" mode", type="cameraMode"))
    resources.addRes(Control(cameraName+"enable", camera, "enable", group="Cameras", label=cameraDisplay+" enable", type="cameraEnable"))
    resources.addRes(Control(cameraName+"record", camera, "record", group="Cameras", label=cameraDisplay+" record", type="cameraRecord"))
    
    # Schedules

    # Start interfaces
    camera.start()
    restServer = RestServer(resources, event=stateChangeEvent, label=cameraDisplay)
    restServer.start()

