audioSink = "alsa_output.0.analog-stereo"
audioSink = "0"

import os
import subprocess
from ha import *

class AudioInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        debug('debugAudio', self.name, "read", addr)
        try:
            if addr == "volume":
                value = subprocess.check_output("ssh pi@localhost pacmd list-sinks|grep volume", shell=True)
                return int(value.split("/")[1].strip(" ").strip("%"))
            elif addr == "mute":
                value = subprocess.check_output("ssh pi@localhost pacmd list-sinks|grep muted", shell=True)
                return 1 if value.split(":")[1].strip(" ").strip("\n") == "yes" else 0
            elif addr == "wifi":
                value = subprocess.check_output("ifconfig wlan0|grep inet\ addr", shell=True)
                return 0 if value == "" else 1
        except:
            return 0

    def write(self, addr, value):
        debug('debugAudio', self.name, "write", addr, value)
        if addr == "volume":
            os.system("ssh pi@localhost pactl set-sink-volume %s %d%%" % (audioSink, value))
        elif addr == "mute":
            os.system("ssh pi@localhost pactl set-sink-mute %s %d" % (audioSink, value))
        elif addr == "wifi":
            if value == 0:
                os.system("/root/carputer/wifi.sh off &")
            else:
                os.system("/root/carputer/wifi.sh on &")


