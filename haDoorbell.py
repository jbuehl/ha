# doorbell sensor
doorbellService = "hostname:7378"
doorbellSensor = "doorbellButton"
doorbellState = 1

# audio alert
soundDir = "/root/sounds/"
doorbellSound = "doorbell.wav"
doorbellRepeat = 1

# sms alert
doorbellNotifyMsg = "Ding dong!"
notifyFromNumber = ""
doorbellNotifyNumbers = []

from ha import *
from ha.rest.restProxy import *
from ha.notify import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    resourceLock = threading.Lock()
    resources = Collection("resources")
    restCache = RestProxy("restProxy", resources, watch=[doorbellService], event=stateChangeEvent, lock=resourceLock)
    restCache.start()
    # Wait for events
    lastState = 0
    while True:
        try:
            state = resources[doorbellSensor].getStateChange()
            debug('debugDoorbell', "state:", state, "lastState", lastState)
            if (state != lastState) and (state == doorbellState):
                smsNotify(doorbellNotifyNumbers, doorbellNotifyMsg)
                for i in range(doorbellRepeat):
                    os.system("aplay "+doorbellDir+doorbellSound)
                state = 0
            lastState = state
        except KeyError:
            debug('debugDoorbell', "no doorbell sensor")
            time.sleep(1)
    
