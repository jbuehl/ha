ignoreServers = ["solar", "power"]

import time
import json
from ha import *
from ha.rest.restProxy import *

if __name__ == "__main__":
    stateChangeEvent = threading.Event()
    resources = Collection("resources")
    resourceStates = ResourceStateSensor("states", None, resources=resources, event=stateChangeEvent)
    restCache = RestProxy("restCache", resources, ignore=ignoreServers, event=stateChangeEvent)
    restCache.start()
    logFileName = logDir+time.strftime("%Y%m%d")+".json"
    lastStates = {}
    while True:
        states = resourceStates.getStateChange()
        changedStates = {}
        for state in states.keys():
            try:
                if states[state] != lastStates[state]:
                    changedStates[state] = states[state]
            except KeyError:
                changedStates[state] = states[state]
        if changedStates != {}:
            lastStates.update(changedStates)
            with open(logFileName, "a") as logFile:
                logFile.write(json.dumps([time.time(), changedStates])+"\n")

