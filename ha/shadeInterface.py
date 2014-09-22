
import time
import threading
from ha.GPIOInterface import *
from ha.HAClasses import *

class ShadeInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)
        self.state = [0, 0, 0, 0]
        self.travelTime = [15, 15, 12, 12]

    def read(self, theAddr):
        try:
            return self.state[theAddr]
        except:
            return 0

    def write(self, theAddr, theValue):
        # Run it asynchronously in a separate thread.
        self.theAddr = theAddr
        self.theValue = theValue
#        self.shadeThread = threading.Thread(target=self.doShade)
#        self.shadeThread.start()
        self.doShade()
        self.state[theAddr] = theValue

    def doShade(self):
        if debugThread: log(self.name, "started")
        self.running = True
        # set the direction
        self.interface.write(GPIOAddr(0,0,self.theAddr*2,1), self.theValue)
        # start the motion
        self.interface.write(GPIOAddr(0,0,self.theAddr*2+1,1), 1)
        # wait for the motion
        time.sleep(self.travelTime[self.theAddr])
        # stop the motion
        self.interface.write(GPIOAddr(0,0,self.theAddr*2+1,1), 0)
        # reset the direction
        self.interface.write(GPIOAddr(0,0,self.theAddr*2,1), 0)
        self.running = False
        if debugThread: log(self.name, "finished")

