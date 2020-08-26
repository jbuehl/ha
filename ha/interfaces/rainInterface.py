# Calculate rainfall using the Peet Tipping Bucket rain gauge
rainIncr = .01

import time
import threading
from ha import *
from ha.interfaces.gpioInterface import *

# global variables
rainSamples = []        # list of times of rainIncr inches sampled
sampleLock = threading.Lock()
sampleEvent = threading.Event()

# rain gauge contact closure interrupt routine
def rainInterrupt(sensor, state):
    global rainSamples, sampleLock, sampleEvent
    curTime = time.time()
    if state == 0:
        with sampleLock:
            rainSamples.append(curTime)
        sampleEvent.set()

class RainInterface(Interface):
    def __init__(self, name, interface, rainGauge, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.rainGauge = rainGauge    # rain gauge contact closure sensor
        self.rainGauge.interrupt = rainInterrupt
        debug("debugRain", self.name, "rainGauge:", self.rainGauge.name)

    def start(self):
        global rainSamples, sampleLock, sampleEvent
        debug("debugRain", self.name, "start")
        # read persistent data
        try:
            samples = self.interface.read("rainSamples")
            if not samples:
                samples = []
        except:
            samples = []
        with sampleLock:
            rainSamples = samples
        # thread to save persistent data
        sampleEvent.clear()
        def saveSamples():
            while True:
                sampleEvent.wait()
                with sampleLock:
                    samples = rainSamples
                debug("debugRain", self.name, "samples", str(samples))
                self.interface.write("rainSamples", samples)
                sampleEvent.clear()
        saveSamplesThread = LogThread(name="saveSamplesThread", target=saveSamples)
        saveSamplesThread.start()

    def read(self, addr):
        global rainSamples, sampleLock, sampleEvent
        # determine how many samples to count
        now = time.time()
        if addr == "minute":
            cutoff = now - 60               # sample period is the last minute
        elif addr == "hour":
            cutoff = now - 3600             # sample period is the last hour
        elif addr == "today":
            today = time.localtime(now)     # sample period is since midnight
            cutoff = time.mktime((today.tm_year,today.tm_mon,today.tm_mday,0,0,0,0,0,0))
        else:
            cutoff = time.time()
        # debug("debugRain", self.name, "read", "addr:", addr, "now:", now, "cutoff:", cutoff)
        # copy the sample list
        with sampleLock:
            samples = rainSamples
        rainTotal = 0.0
        for sample in reversed(samples):
            if sample > cutoff: # sample is within the sample period
                rainTotal += rainIncr
            else:               # return the total
                break
        # debug("debugRain", self.name, "read", "rainTotal:", rainTotal)
        return rainTotal

    def write(self, addr, value):
        global rainSamples, sampleLock, sampleEvent
        debug("debugRain", self.name, "write", "addr:", addr, "value:", value)
        if addr == "reset":
            # reset the sample list
            with sampleLock:
                rainSamples = []
            sampleEvent.set()
