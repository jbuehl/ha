from ha.HAClasses import *
from ha.cameraInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    camera = CameraInterface("Camera", event=stateChangeEvent)
    
    # Cameras
    resources.addRes(Camera("camera", camera, None, group="Cameras", label="Camera", type="camera"))
    
    # Schedules

    # Start interfaces
    camera.start()
    restServer = RestServer(resources, event=stateChangeEvent)
    restServer.start()

