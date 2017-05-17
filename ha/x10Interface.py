import x10
import time
from ha import *

class X10Interface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.state = {"A1":0, "A2":0, "A3":0, "A4":0, "A5":0, "A6":0, "A7":0, "A8":0}
        self.stateFileName = "x10.state"
        self.readState()

    def start(self):
        debug('debugThread', self.name, "started")

    def read(self, addr):
        try:
            return self.state[addr]
        except:
            return 0
        
    def write(self, addr, value):
        if value:
            state = "On"
        else:
            state = "Off"
        debug('debugLights', self.name,  addr, state)
        x10.sendCommands(self.interface.device, addr+" "+state)
        self.state[addr] = value
        self.writeState()
        time.sleep(.5)      # delay to enhance reliability - FIXME
    
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
                

