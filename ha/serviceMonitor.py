serviceMonitorInterval = 2

import threading
import time
from ha import *
from ha.notification import *

def watchServices(resources, notifyNumbers, timeout=60):
    serviceUpTimes = {}
    def serviceWatch():
        debug("debugServiceMonitor", "serviceMonitor", "starting")
        while True:
            with resources.lock:
                monitoredGroups = []
                if resources["alertServices"].getState():
                    monitoredGroups.append("Services")
                if resources["alertDoors"].getState():
                    monitoredGroups.append("Doors")
                debug("debugServiceMonitor", "serviceMonitor", str(monitoredGroups))
                for resource in resources:
                    if isinstance(resources[resource].group, list):
                        group = resources[resource].group[0]
                    else:
                        group = resources[resource].group
                    if group in monitoredGroups:
                        debug("debugServiceMonitor", "serviceMonitor", resource, group, resources[resource].state)
                        if group == "Services":
                            if resources[resource].state == 1:  # service is up
                                serviceUpTimes[resource] = time.time()
                            else:
                                try:        # send notification if service was previously up
                                    if time.time() - serviceUpTimes[resource] > timeout:
                                        msg = "service "+resources[resource].label+" is down"
                                        debug("debugServiceMonitor", "serviceMonitor", msg)
                                        smsNotify(notifyNumbers, msg)
                                        serviceUpTimes[resource] = float("inf")
                                except KeyError:    # service is down at the start
                                    serviceUpTimes[resource] = float("inf")
                        elif (group == "Doors") and (resource[-5:] != "Doors"):
                            if resources[resource].state == 0:  # door is closed
                                serviceUpTimes[resource] = time.time()
                            else:
                                try:        # send notification if door was previously closed
                                    if time.time() - serviceUpTimes[resource] > 2:
                                        msg = resources[resource].label+" door is open"
                                        debug("debugServiceMonitor", "serviceMonitor", msg)
                                        smsNotify(notifyNumbers, msg)
                                        serviceUpTimes[resource] = float("inf")
                                except KeyError:    # service is down at the start
                                    serviceUpTimes[resource] = float("inf")
            time.sleep(serviceMonitorInterval)

    serviceWatchThread = threading.Thread(target=serviceWatch)
    serviceWatchThread.start()
