doorbellService = "192.168.1.52:7378"
doorbellSensor = "doorbellButton"
doorbellState = 1
doorbellSound = "doorbell2.wav"
doorbellRepeat = 1

doorbellDir = "/root/doorbell/"

from ha import *
from ha.interfaces.restInterface import *

if __name__ == "__main__":
    # Resources
    resources = Collection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    restInterface = RestInterface("rest", None, service=doorbellService, event=stateChangeEvent)
    
    # Sensors
    doorbell = Sensor(doorbellSensor, restInterface, "/resources/"+doorbellSensor+"/state")

    # Wait for events
    lastState = 0
    while True:
        state = doorbell.getStateChange()
        debug('debugDoorbell', "doorbellState", state, lastState)
        if state != lastState:
            if state == doorbellState:
                for i in range(doorbellRepeat):
                    os.system("aplay "+doorbellDir+doorbellSound)
                state = 0
        lastState = state
    
