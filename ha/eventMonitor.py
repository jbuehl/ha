
import threading
import time
from ha import *
from ha.notification.notificationServer import *
from ha.camera.events import *

def watchEvents(resources, timeout=60):
    serviceUpTimes = {}
    resourceGroups = {}
    def serviceWatch():
        debug("debugEventMonitor", "eventMonitor", "starting")
        while True:
            # wait for a state change
            resourceStates = resources.getState(wait=True)

            # check for services that have gone down
            groupResources = resources.getGroup("Services")
            for resource in groupResources:
                if resourceStates[resource.name] == 1:          # service is up
                    serviceUpTimes[resource.name] = time.time()
                else:
                    try:        # check if the service is down and was previously up
                        now = time.time()
                        if now - serviceUpTimes[resource.name] > timeout:   # service has been down for timeout
                            debug("debugEventMonitor", "service down", resource.label, serviceUpTimes[resource.name])
                            # send a notification if this alert is enabled
                            if resourceStates["alertServices"]:
                                msg = "service "+resource.label+" is down"
                                notify(resources, "alertServices", msg)
                            serviceUpTimes[resource.name] = float("inf")    # prevent the message from repeating
                    except KeyError:    # service is down at the start
                        serviceUpTimes[resource.name] = float("inf")

            # check for door and motion events
            groupResources = resources.getGroup("Doors")
            for resource in groupResources:
                if (resource.name[-5:] != "Doors") and (resource.name != "doorbell"):
                    try:
                        resourceState = resourceStates[resource.name]
                    except KeyError:    # states haven't been updated yet
                        break
                    if resourceState == 0:  # door is closed
                        serviceUpTimes[resource.name] = time.time()
                    else:
                        try:        # create event if door was previously closed
                            if time.time() - serviceUpTimes[resource.name] > 1:
                                eventType = resource.type
                                eventTime = time.strftime("%Y%m%d%H%M%S")
                                # associate the event with a camera
                                if resource.name in ["frontDoor", "frontPorchMotionSensor"]:
                                    camera = "frontdoor"
                                elif resource.name in ["garageDoor", "drivewayMotionSensor"]:
                                    camera = "driveway"
                                elif resource.name in ["garageBackDoor", "southSideMotionSensor"]:
                                    camera = "southside"
                                elif resource.name in ["northSideMotionSensor"]:
                                    camera = "northside"
                                elif resource.name in ["familyRoomDoor", "masterBedroomDoor", "deckMotionSensor"]:
                                    camera = "deck"
                                elif resource.name in ["backHouseDoor", "backHouseMotionSensor"]:
                                    camera = "backhouse"
                                else:
                                    camera = ""
                                debug("debugEventMonitor", "eventMonitor", resource.name, eventType, eventTime, camera)
                                if camera != "":
                                    createEvent(eventType, camera, eventTime)
                                # send a notification if enabled
                                msg =  ""
                                if (resourceStates["alertDoors"]) and (eventType == "door"):
                                    msg = resource.label+" door is open"
                                    notifyType = "alertDoors"
                                elif (resourceStates["alertMotion"]) and (eventType == "motion"):
                                    msg = resource.label
                                    notifyType = "alertMotion"
                                if msg != "":
                                    if camera != "":
                                        msg += " https://shadyglade.thebuehls.com/"
                                        msg += "image/"+camera+"/"+eventTime[0:8]+"/"
                                        msg += eventTime+"_"+eventType
                                    notify(resources, notifyType, msg)
                                serviceUpTimes[resource.name] = float("inf")
                        except KeyError:    # service is down at the start
                            serviceUpTimes[resource.name] = float("inf")

    serviceWatchThread = threading.Thread(target=serviceWatch)
    serviceWatchThread.start()
