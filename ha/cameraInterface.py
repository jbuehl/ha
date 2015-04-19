# Camera interface

# Functions:
#    get/set attributes
#    enable/disable camera
#    take picture
#    start/stop video
#    start/stop motion detection
#    get image
#    get video

import subprocess
from ha.HAClasses import *

class CameraInterface(HAInterface):
    def __init__(self, name, interface=None, event=None):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.bus = bus

    def read(self, addr):
        try:
            debug('debugI2C', self.name, "readByte", addr)
            return int(subprocess.check_output("i2cget -y %d %d %d b"%(self.bus, addr[0], addr[1]),shell=True),16)
        except:
            return 0

    def write(self, addr, value):
        debug('debugI2C', self.name, "writeByte", addr, value)
        subprocess.check_output("i2cset -y %d %d %d %d b"%(self.bus, addr[0], addr[1], value),shell=True)

