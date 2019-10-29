
import subprocess
from ha import *

# Interface to various environment variables
class EnvInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        if addr == "cpuTemp":
            value = float(subprocess.check_output("vcgencmd measure_temp", shell=True)[5:-3])
        elif addr[1:4] == "mnt":
            value = int(subprocess.check_output("df -h "+addr, shell=True).decode().split("\n")[1].split()[4].strip("%"))
        return value
