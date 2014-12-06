import x10
import time
from ha.HAClasses import *

class X10Interface(HAInterface):
    def __init__(self, theName, serialInterface):
        HAInterface.__init__(self, theName, serialInterface)
        self.state = {"A1":0, "A2":0, "A3":0, "A4":0, "A5":0, "A6":0, "A7":0, "A8":0}
        self.stateFileName = "x10.state"
        self.readState()

    def start(self):
        if debugThread: log(self.name, "started")
#        self.interface = ""
#        try:
#            self.interface = serialInterface.interface
#            HCInterface.__init__(self, theName, theApp, serialInterface)
#            if debugThread: log(self.name, "started")
#        except:
#            log("Error opening X10 interface on", self.device)

    def read(self, theAddr):
        try:
            return self.state[theAddr]
        except:
            return 0
        
    def write(self, theAddr, theValue):
        if theValue:
            state = "On"
        else:
            state = "Off"
        if debugLights: log(self.name,  theAddr, state)
        x10.sendCommands(self.interface.interface, theAddr+" "+state)
        self.state[theAddr] = theValue
        self.writeState()
    
    def readState(self):
        try:
            stateFile = open(self.stateFileName)
            for line in stateFile:
                try:
                    line = line[:line.find("#")].strip()
                    if line != "":
                        param = line.split("=")
                        self.state[param[0].strip()] = eval(param[1].strip())
                except:
                    pass
            stateFile.close()
        except:
            pass

    def writeState(self):
        stateFile = open(self.stateFileName, "w")
        for device in self.state.keys():
            stateFile.write(device+" = "+str(self.state[device])+"\n")
        stateFile.close()
                

