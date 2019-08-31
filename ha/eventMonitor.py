serviceMonitorInterval = 1

import threading
import time
from ha import *
from ha.notification import *

def watchEvents(resources, notifyNumbers, timeout=60):
    serviceUpTimes = {}
    def serviceWatch():
        debug("debugEventMonitor", "eventMonitor", "starting")
        while True:
            with resources.lock:
                monitoredGroups = []
                if resources["alertServices"].getState():
                    monitoredGroups.append("Services")
                if resources["alertDoors"].getState():
                    monitoredGroups.append("Doors")
                debug("debugEventMonitor", "eventMonitor", str(monitoredGroups))
                for resource in resources:
                    if isinstance(resources[resource].group, list):
                        group = resources[resource].group[0]
                    else:
                        group = resources[resource].group
                    if group in monitoredGroups:
                        debug("debugEventMonitor", "eventMonitor", resource, group, resources[resource].state)
                        if group == "Services":
                            if resources[resource].state == 1:  # service is up
                                serviceUpTimes[resource] = time.time()
                            else:
                                try:        # send notification if service was previously up
                                    if time.time() - serviceUpTimes[resource] > timeout:
                                        msg = "service "+resources[resource].label+" is down"
                                        debug("debugEventMonitor", "eventMonitor", msg)
                                        notify(resources, "alertServices", msg)
                                        serviceUpTimes[resource] = float("inf")
                                except KeyError:    # service is down at the start
                                    serviceUpTimes[resource] = float("inf")
                        elif (group == "Doors") and (resource[-5:] != "Doors") and (resource != "doorbell"):
                            if resources[resource].state == 0:  # door is closed
                                serviceUpTimes[resource] = time.time()
                            else:
                                try:        # send notification if door was previously closed
                                    if time.time() - serviceUpTimes[resource] > 1:
                                        msg = resources[resource].label+" door is open"
                                        debug("debugEventMonitor", "eventMonitor", msg)
                                        notify(resources, "alertDoors", msg)
                                        serviceUpTimes[resource] = float("inf")
                                except KeyError:    # service is down at the start
                                    serviceUpTimes[resource] = float("inf")
            time.sleep(serviceMonitorInterval)

    serviceWatchThread = threading.Thread(target=serviceWatch)
    serviceWatchThread.start()
