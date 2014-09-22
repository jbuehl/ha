import serial
import sys
from ha.HAClasses import *
from ha.logging import *

class HASerialInterface(HAInterface):
    def __init__(self, theName, theInterface, serialConfig):
        HAInterface.__init__(self, theName, theInterface)
        self.serialConfig = serialConfig

    def start(self):
        if self.interface == "/dev/stdin":
            log(self.name, "using stdin", self.interface)
            self.inPort = sys.stdin
            self.outPort = sys.stdout
        else:
            try:
                log(self.name, "opening serial port", self.interface)
                self.inPort = self.outPort = serial.Serial(self.interface, **self.serialConfig)
            except:
                log(self.name, "unable to open serial port")
                return
        
    def stop(self):
        if self.interface != "/dev/stdin":
            self.inPort.close()

    def read(self, theAddr, theLen=1):
        return self.inPort.read(theLen)

    def write(self, theAddr, theValue):
        self.outPort.write(theValue)
            
    def readline(self, theAddr):
        return self.inPort.readline()

    def writeline(self, theAddr, theValue):
        self.outPort.writeline(theValue)
            

