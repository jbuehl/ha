serviceMonitorInterval = 10

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
                for resource in resources:
                    if resource.split(".")[0] == "services":
                        serviceName = resource.split(".")[1]
                        debug("debugServiceMonitor", "serviceMonitor", serviceName, resources[resource].state)
                        if resources[resource].state == 1:  # service is up
                            serviceUpTimes[serviceName] = time.time()
                        else:
                            try:        # send notification if service was previously up
                                if time.time() - serviceUpTimes[serviceName] > timeout:
                                    serviceLabel = resources[resource].label
                                    msg = "service "+serviceLabel+" is down"
                                    debug("debugServiceMonitor", "serviceMonitor", msg)
                                    smsNotify(notifyNumbers, msg)
                                    serviceUpTimes[serviceName] = float("inf")
                            except KeyError:    # service is down at the start
                                serviceUpTimes[serviceName] = float("inf")
            time.sleep(serviceMonitorInterval)
                            
    serviceWatchThread = threading.Thread(target=serviceWatch)
    serviceWatchThread.start()
        
