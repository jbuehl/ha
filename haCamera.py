from ha.HAClasses import *
from ha.cameraInterface import *
from ha.restServer import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    camera = CameraInterface("Camera", event=stateChangeEvent)
    
    # Temperature
    resources.addRes(HASensor("edisonTemp", temp, 0x4b, group="Temperature", label="Edison temp", type="tempF"))
    
    # Schedules

    # Start interfaces
    camera.start()
    restServer = RestServer(resources, event=stateChangeEvent)
    restServer.start()

