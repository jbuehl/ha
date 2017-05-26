doorbellService = "hostname:7378"
doorbellSensor = "doorbellButton"
doorbellState = 1
doorbellSound = "doorbell.wav"
doorbellRepeat = 1

doorbellDir = "/root/doorbell/"

from ha import *
from ha.rest.restProxy import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    resourceLock = threading.Lock()
    resources = Collection("resources")
    restCache = RestProxy("restProxy", resources, [], stateChangeEvent, resourceLock, watch=[doorbellService])
    restCache.start()
    # Wait for events
    lastState = 0
    while True:
        try:
            state = resources[doorbellSensor].getStateChange()
            debug('debugDoorbell', "state:", state, "lastState", lastState)
            if state != lastState:
                if state == doorbellState:
                    for i in range(doorbellRepeat):
                        os.system("aplay "+doorbellDir+doorbellSound)
                    state = 0
            lastState = state
        except KeyError:
            debug('debugDoorbell', "no doorbell")
            time.sleep(1)
    
