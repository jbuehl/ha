# doorbell sensor
doorbellService = "hostname:7378"
doorbellSensor = "doorbellButton"
doorbellState = 1

# audio alert
doorbellSound = "doorbell.wav"
doorbellRepeat = 1

# sms alert
doorbellNotifyMsg = "Doorbell https://shadyglade.thebuehls.com/image?camera=%s&image=%s"
notifyFromNumber = ""
doorbellNotifyNumbers = []

# camera
camera = "camera1"

import subprocess
import urllib
from ha import *
from ha.rest.restProxy import *
from ha.notify import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    debug('debugDoorbell', "watching", doorbellService+"/"+doorbellSensor)
    resources = Collection("resources")
    restCache = RestProxy("restProxy", resources, watch=[doorbellService], event=stateChangeEvent)
    restCache.start()
    # Wait for events
    lastState = 0
    while True:
        try:
            state = resources[doorbellSensor].getStateChange()
            debug('debugDoorbell', "state:", state, "lastState", lastState)
            if (state != lastState) and (state == doorbellState):
                for i in range(doorbellRepeat):
                    debug('debugDoorbell', "playing", soundDir+doorbellSound)
                    os.system("aplay "+soundDir+doorbellSound)
                debug('debugDoorbell', "notifying", str(doorbellNotifyNumbers))
                imageFileName = urllib.quote(subprocess.check_output("ssh pluto.local ls -1 /var/ftp/images/"+camera+"/*.jpg | tail -n1", shell=True).split("/")[-1].strip("\n"))
                smsNotify(doorbellNotifyNumbers, doorbellNotifyMsg%(camera, imageFileName))
                state = 0
            lastState = state
        except KeyError:
            debug('debugDoorbell', "no doorbell sensor")
            time.sleep(1)
    
