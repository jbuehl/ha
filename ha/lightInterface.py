import json
from ha.GPIOInterface import *
from ha.HAClasses import *

class LightInterface(HAInterface):
    def __init__(self, name, interface):
        HAInterface.__init__(self, name, interface)
        self.stateFile = stateDir+name+".state"

    def start(self):
        # read the state from the file if it exists
        try:
            self.state = json.load(open(self.stateFile))
        except:
            self.state = {}
        # set the state of all the devices on the interface
        for addr in self.state.keys():
            self.interface.write(GPIOAddr(0, 0, addr, 1), self.state[addr])

    def read(self, addr):
        try:
            return self.state[addr]
        except:
            # if the device does not exist, create it and set the state to 0
            self.write(addr, 0)
            return 0

    def write(self, addr, value):
        # set the state of the device and save it
        self.interface.write(GPIOAddr(0, 0, addr, 1), value)
        self.state[addr] = value
        json.dump(self.state, open(self.stateFile, "w"))

