#!/usr/bin/env python
# Print the messages that are sent to advertise REST services

restBeaconPort = 4242

import socket
import json
import time
import sys

if __name__ == "__main__":
    beaconSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    beaconSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    beaconSocket.bind(("", restBeaconPort))
    while True:
        (data, addr) = beaconSocket.recvfrom(8192)   # FIXME - need to handle arbitrarily large data
        print time.asctime(time.localtime()), "addr:", addr, "data:", data
#        try:
#            serviceData = json.loads(data)
#            print "  hostname:", serviceData[0]
#            print "  port:", serviceData[1]
#            print "  resources:", serviceData[2]
#            print "  timestamp:", time.asctime(time.localtime(serviceData[3]))
#            print "  label:", serviceData[4]
#        except:
#            pass
#        print
        sys.stdout.flush()

