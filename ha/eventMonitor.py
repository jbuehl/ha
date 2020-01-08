serviceMonitorInterval = .1

import threading
import time
from ha import *
from ha.notification.notificationServer import *
from ha.camera.events import *

def watchEvents(resources, notifyNumbers, timeout=60):
    serviceUpTimes = {}
    def serviceWatch():
        debug("debugEventMonitor", "eventMonitor", "starting")
        while True:
            with resources.lock:
                monitoredGroups = ["Services", "Doors"]
                for resource in resources:
                    if isinstance(resources[resource].group, list):
                        group = resources[resource].group[0]
                    else:
                        group = resources[resource].group
                    if group in monitoredGroups:
                        # debug("debugEventMonitor", "eventMonitor", resource, group, resources[resource].state)
                        if group == "Services":
                            if resources[resource].state == 1:  # service is up
                                serviceUpTimes[resource] = time.time()
                            else:
                                try:        # send notification if service was previously up
                                    now = time.time()
                                    if now - serviceUpTimes[resource] > timeout:
                                        log("eventMonitor", "service down", resources[resource].label, serviceUpTimes[resource])
                                        # send a notification if enabled
                                        if resources["alertServices"].getState():
                                            msg = "service "+resources[resource].label+" is down"
                                            debug("debugEventMonitor", "eventMonitor", resources[resource].label, now, serviceUpTimes[resource])
                                            notify(resources, "alertServices", msg)
                                        serviceUpTimes[resource] = float("inf")
                                except KeyError:    # service is down at the start
                                    log("eventMonitor", "adding service", resources[resource].label)
                                    serviceUpTimes[resource] = float("inf")
                        elif (group == "Doors") and (resource[-5:] != "Doors") and (resource != "doorbell"):
                            if resources[resource].state == 0:  # door is closed
                                serviceUpTimes[resource] = time.time()
                            else:
                                try:        # create event if door was previously closed
                                    if time.time() - serviceUpTimes[resource] > 1:
                                        eventType = resources[resource].type
                                        eventTime = time.strftime("%Y%m%d%H%M%S")
                                        if resource == "frontDoor":
                                            camera = "frontdoor"
                                        elif resource in ["garageDoor", "drivewayMotionSensor"]:
                                            camera = "driveway"
                                        elif resource == "garageBackDoor":
                                            camera = "southside"
                                        elif resource in ["familyRoomDoor", "masterBedroomDoor"]:
                                            camera = "deck"
                                        elif resource == "backHouseDoor":
                                            camera = "backhouse"
                                        else:
                                            camera = ""
                                        debug("debugEventMonitor", "eventMonitor", resource, eventType, eventTime, camera)
                                        if camera != "":
                                            createEvent(eventType, camera, eventTime)
                                        # send a notification if enabled
                                        msg =  ""
                                        if (resources["alertDoors"].getState()) and (eventType == "door"):
                                            msg = resources[resource].label+" door is open"
                                            notifyType = "alertDoors"
                                        elif (resources["alertMotion"].getState()) and (eventType == "motion"):
                                            msg = resources[resource].label.split(" ")[0]+" motion"
                                            notifyType = "alertMotion"
                                        if msg != "":
                                            if camera != "":
                                                msg += " https://shadyglade.thebuehls.com/"
                                                msg += "image/"+camera+"/"+eventTime[0:8]+"/"
                                                msg += eventTime+"_"+eventType
                                            notify(resources, notifyType, msg)
                                        serviceUpTimes[resource] = float("inf")
                                except KeyError:    # service is down at the start
                                    serviceUpTimes[resource] = float("inf")
            time.sleep(serviceMonitorInterval)

    serviceWatchThread = threading.Thread(target=serviceWatch)
    serviceWatchThread.start()
