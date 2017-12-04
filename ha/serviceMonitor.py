serviceMonitorInterval = 10

import threading
import time
from ha import *
from ha.notification import *

def watchServices(resources, notifyNumbers, timeout=60):
    serviceUpTimes = {}
    def serviceWatch():
        debug("debugServiceMonitor", "starting serviceWatch")
        while True:
            for resource in resources:
                if resource.split(".")[0] == "services":
                    serviceName = resource.split(".")[1]
#                    debug("debugServiceMonitor", serviceName, resources[resource].state)
                    if resources[resource].state == 1:  # service is up
                        serviceUpTimes[serviceName] = time.time()
                    else:
                        try:        # send notification is service was previously up
                            if time.time() - serviceUpTimes[serviceName] > 20: #timeout:
                                msg = "service "+resource.split(".")[1]+" is down"
                                debug("debugServiceMonitor", msg)
                                smsNotify(notifyNumbers, msg)
                                serviceUpTimes[serviceName] = float("inf")
                        except KeyError:    # service is down at the start
                            serviceUpTimes[serviceName] = float("inf")
            debug("debugServiceMonitor", str(serviceUpTimes))
            time.sleep(serviceMonitorInterval)
                            
    serviceWatchThread = threading.Thread(target=serviceWatch)
    serviceWatchThread.start()
        
