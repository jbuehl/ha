import threading
import time
from ha import *

class TempInterface(Interface):
    def __init__(self, name, interface=None, sample=1):
        Interface.__init__(self, name, interface)
        self.sample = sample

    def start(self):
        # data sampling thread
        def readData():
            debug('debugTemp', self.name, "readData started")
            temp = self.readData()    # initialize states with a reading
            samples = 1
            lastMinute = -1
            # sample once per second and update states with the average every minute
            while True:
                thisMinute = int(time.strftime("%M"))
                debug('debugTemp', self.name, "thisMinute", thisMinute, "lastMinute", lastMinute)
                if thisMinute != lastMinute:                    # start of a new minute
                    for addr in list(self.sensorAddrs.keys()):    # average the readings
                        self.states[addr] = temp[addr]/samples
                        temp[addr] = 0.0
                    if self.event:
                        self.event.set()
                    debug('debugTemp', self.name, "state", self.states, "samples", samples)
                    samples = 0
                    lastMinute = thisMinute
                sample = self.readData()            # take another sample
                for addr in list(sample.keys()):
                    try:
                        temp[addr] += sample[addr]
                    except KeyError:                # a sensor was added during the sample period
                        temp[addr] = sample[addr]
                samples += 1
                time.sleep(self.sample)

        readStatesThread = LogThread(name="readStatesThread", target=readData)
        readStatesThread.start()

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        return self.states[addr]

    # take a reading of all sensors
    def readData(self):
        temp = {}
        for addr in list(self.sensorAddrs.keys()):
            temp[addr] = self.interface.read(addr)
        debug('debugTemp', self.name, "readData", temp)
        return temp
