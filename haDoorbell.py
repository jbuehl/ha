doorbellService = "192.168.1.52:7378"
doorbellSensor = "doorbellButton"
doorbellState = 1
doorbellSound = "doorbell2.wav"
doorbellRepeat = 1

#doorbellService = "192.168.1.59:7378"
#doorbellSensor = "spa"
#doorbellState = 1
#doorbellSound = "the\ spa\ is\ ready.wav"

#doorbellService = "192.168.1.50:7378"
#doorbellSensor = "familyRoomDoor"
#doorbellState = 1
#doorbellSound = "the\ spa\ is\ ready.wav"

doorbellDir = "/root/doorbell/"

from ha.HAClasses import *
from ha.restInterface import *

if __name__ == "__main__":
    # Resources
    resources = HACollection("resources")

    # Interfaces
    stateChangeEvent = threading.Event()
    restInterface = HARestInterface("rest", None, service=doorbellService, event=stateChangeEvent)
    
    # Sensors
    doorbell = HASensor(doorbellSensor, restInterface, "/resources/"+doorbellSensor+"/state")

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
    
