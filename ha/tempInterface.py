import threading
import time
from ha.HAClasses import *

class TempInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)

    def start(self):
        def readData():
            debug('debugTemp', self.name, "readData started")
            while running:
                debug('debugTemp', self.name, "waiting", tempPollInterval)
                time.sleep(tempPollInterval)
                self.readData()
        readStatesThread = threading.Thread(target=readData)
        readStatesThread.start()

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        return self.states[self.sensorAddrs[addr].name]

    def readData(self):
        debug('debugTemp', self.name, "readData sensors", self.sensors, self.sensorAddrs)
        for sensor in self.sensors.keys():
            self.states[sensor] = self.interface.read(self.sensors[sensor].addr)
        debug('debugTemp', self.name, "readData states", self.states)
        if self.event:
            self.event.set()

