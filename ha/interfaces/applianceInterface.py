import json
from ha.interfaces.gpioInterface import *
from ha import *

class ApplianceInterface(Interface):
    def __init__(self, name, interface):
        Interface.__init__(self, name, interface)
        self.stateFile = stateDir+name+".state"

    def start(self):
        # read the state from the file if it exists
        try:
            self.state = json.load(open(self.stateFile))
            debug('debugState', self.name, "reading", self.stateFile, self.state)
        except:
            self.state = {}
        # set the state of all the devices on the interface
        for addr in list(self.state.keys()):
            # addr must be converted to int because json stringified it when dumped
            self.interface.write(int(addr), self.state[addr])

    def read(self, addr):
        try:
            return self.state[str(addr)]    # keys are saved as strings
        except:
            # if the device does not exist, create it and set the state to 0
            self.write(addr, 0)
            return 0

    def write(self, addr, value):
        # set the state of the device and save it
        self.interface.write(addr, value)
        self.state[str(addr)] = value   # keys are saved as strings
        debug('debugState', self.name, "writing", self.stateFile, self.state)
        json.dump(self.state, open(self.stateFile, "w"))

