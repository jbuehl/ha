#!/usr/bin/env python
# Print the messages that are sent to advertise REST service states
from __future__ import print_function

multicast = False
multicastGroup = "224.0.0.1"
restStatePort = 4243

import socket
import json
import time
import sys
import struct

if __name__ == "__main__":
    if multicast:
        restAddr = multicastGroup
    else:
        restAddr = ""
    beaconSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    beaconSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    beaconSocket.bind((restAddr, restStatePort))
    if multicast:
        beaconSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                struct.pack("4sl", socket.inet_aton(multicastGroup), socket.INADDR_ANY))
    seqDir = {}
    while True:
        (data, addr) = beaconSocket.recvfrom(8192)   # FIXME - need to handle arbitrarily large data
        state = json.loads(str(data, "utf-8"))
        print(time.asctime(time.localtime()), "addr:", addr, "hostname:", state["hostname"], "port:", state["port"], end=' ')
        try:
            hostname = state["hostname"]
            seq = int(state["seq"])
            print("seq:", seq, end=' ')
            try:
                if seq != seqDir[hostname] + 1:
                    print("***")
                else:
                    print("")
            except KeyError:
                print("")
            seqDir[hostname] = seq
        except KeyError:
            print("")
        sys.stdout.flush()
