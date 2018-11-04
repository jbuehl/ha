#!/usr/bin/env python
# Print the messages that are sent to advertise REST service states

restStatePort = 4243

import socket
import json
import time
import sys

if __name__ == "__main__":
    beaconSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    beaconSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    beaconSocket.bind(("", restStatePort))
    while True:
        (data, addr) = beaconSocket.recvfrom(8192)   # FIXME - need to handle arbitrarily large data
        print time.asctime(time.localtime()), "addr:", addr, "data:", data
        sys.stdout.flush()
        
