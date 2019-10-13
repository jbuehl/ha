
import subprocess
from ha import *

# Interface to various environment variables
class EnvInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        if addr == "cpuTemp":
            value = float(subprocess.check_output("vcgencmd measure_temp", shell=True)[5:-3])
        return value
