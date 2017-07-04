import socket
from ha import *
from ha.interfaces.cameraInterface import *
from ha.rest.restServer import *

if __name__ == "__main__":
    # Environment
    cameraName = socket.gethostname()
    cameraDisplay = cameraName[:-1].capitalize()+" "+cameraName[-1]

    # Interfaces
    stateChangeEvent = threading.Event()
    camera = CameraInterface(cameraName, imageDir=imageDir, rotation=cameraRotation, event=stateChangeEvent)
    
    # Cameras
    cameraImage = Sensor(cameraName+"image", camera, "image", group="Cameras", label=cameraDisplay, type="image")
    cameraThumb = Sensor(cameraName+"thumb", camera, "thumb", group="Cameras", label=cameraDisplay+" thumbnail", type="image")
    cameraMode = Control(cameraName+"mode", camera, "mode", group="Cameras", label=cameraDisplay+" mode", type="cameraMode")
    cameraEnable = Control(cameraName+"enable", camera, "enable", group="Cameras", label=cameraDisplay+" enable", type="cameraEnable")
    cameraRecord = Control(cameraName+"record", camera, "record", group="Cameras", label=cameraDisplay+" record", type="cameraRecord")
    
    # Schedules

    # Resources
    resources = Collection("resources", [cameraImage, cameraThumb, cameraMode, cameraEnable, cameraRecord])
    restServer = RestServer(resources, event=stateChangeEvent, label=cameraDisplay)

    # Start interfaces
    camera.start()
    restServer.start()

