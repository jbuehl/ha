import os
import subprocess
import time
from ha import *

class FireplaceInterface(Interface):
    def __init__(self, name, interface, videoControl, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.videoControl = videoControl
        self.state = False
        self.pid = 0

    def read(self, addr):
        return self.state

    def write(self, addr, value):
        if value:
            video = self.videoControl.getState()
            cmd = "/usr/bin/mplayer -really-quiet -fs -lavdopts threads=4 -loop 0 -vo fbdev /video/"+video+".mp4"
            self.pid = subprocess.Popen(cmd, shell=True).pid+1
            log("pid", self.pid)
        else:
            if self.pid:
                os.popen("kill "+str(self.pid))
            time.sleep(1)
            os.popen("dd if=/dev/zero of=/dev/fb0")
            os.popen("setterm -cursor off > /dev/tty1")
        self.state = value
