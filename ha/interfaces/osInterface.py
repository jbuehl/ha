
import subprocess
from ha import *

# Interface to various OS parameters
class OSInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def read(self, addr):
        addrParts = addr.split()
        if addrParts[0] == "cpuTemp":
            return float(subprocess.check_output("vcgencmd measure_temp", shell=True)[5:-3])
        elif addrParts[0] == "diskUse":
            return int(subprocess.check_output("df -h "+addrParts[1], shell=True).decode().split("\n")[1].split()[4].strip("%"))
        elif addrParts[0] == "ssid":
            try:
                return subprocess.check_output("iwconfig "+addrParts[1]+"|grep ESSID", shell=True).decode().strip("\n").split(":")[-1].split("/")[0].strip().strip('"')
            except subprocess.CalledProcessError:
                return ""
        elif addrParts[0] == "ipAddr":
            try:
                return subprocess.check_output("ifconfig "+addrParts[1]+"|grep inet\ ", shell=True).decode().strip("\n").split()[1]
            except subprocess.CalledProcessError:
                return ""
        elif addrParts[0] == "uptime":
            return " ".join(c for c in subprocess.check_output("uptime", shell=True).decode().strip("\n").split(",")[0].split()[2:])
        else:
            return None
