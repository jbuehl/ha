# Samsung TV remote interface
# https://github.com/Ape/samsungctl

import samsungctl
from ha import *

keyCmds = {
    "off": "KEY_POWEROFF",
    "sleep": "KEY_POWEROFF",
    "sleeping": "KEY_POWEROFF",
    "mute": "KEY_MUTE",
    "dumb": "KEY_MUTE",
    "stun": "KEY_MUTE",
    "unmute": "KEY_MUTE",
    "talkative": "KEY_MUTE",
    "antenna": "KEY_TV",                        # antenna
    "broadcast": "KEY_TV",                      # antenna
    "roku": "KEY_EXT20",                        # HDMI1
    "chromecast": "KEY_AUTO_ARC_PIP_WIDE",      # HDMI2
    "chrome": "KEY_AUTO_ARC_PIP_WIDE",          # HDMI2
    "hdmi3": "KEY_AUTO_ARC_PIP_RIGHT_BOTTOM",   # HDMI3
    "hdmi4": "KEY_AUTO_ARC_AUTOCOLOR_FAIL",     # HDMI4
    "component": "KEY_COMPONENT1",              # component
    "pc": "KEY_PCMODE",                         # VGA
}

config = {
    "name": "ha",
    "description": "PC",
    "id": "",
    "host": "192.168.1.103",
    "port": 55000,
    "method": "legacy",
    "timeout": 0,
}

class SamsungInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)

    def write(self, addr, value):
        debug('debugSamsung', self.name, "write", addr, value)
        try:
            if value == 0:
                value = "off"
            keyCmd = keyCmds[value.lower()]
            samsungctl.Remote(config).control(keyCmd)
        except KeyError:
            log(self.name, addr, "unknown command", value)
