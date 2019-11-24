import socket
import json
import struct
import threading
import time
from ha import *

# TP-Link device control

port = 9999

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
def encrypt(string):
    msg = bytes(string, "utf-8")
    result = struct.pack('>I', len(msg))
    key = 171
    for i in msg:
        a = key ^ int(i)
        key = a
        result += bytes([a])
    return result

def decrypt(msg):
    result = b""
    key = 171
    for i in msg[4:]:
        a = key ^ int(i)
        key = i
        result += bytes([a])
    return result.decode("utf-8")

class TplinkInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface, event=event)
        # poll sensors every second to generate state change notifications
        # cached state is the dictionary that is returned
        def getStates():
            while True:
                for sensor in list(self.sensors.values()):
                    try:
                        (ipAddr, attr) = sensor.addr.split(",")
                    except ValueError: # ignore sensors with an attribute so devices are only polled once
                        ipAddr = sensor.addr.split(",")[0]
                        state = self.readState(ipAddr)
                        if state != self.states[ipAddr]:
                            self.states[ipAddr] = state
                            sensor.notify()
                time.sleep(1)
        stateThread = threading.Thread(target=getStates)
        stateThread.start()

    def readState(self, ipAddr):
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.connect((ipAddr, port))
            sock_tcp.send(encrypt('{"system":{"get_sysinfo":{}}}'))
            state = json.loads(decrypt(sock_tcp.recv(2048)))["system"]["get_sysinfo"]
            sock_tcp.close()
            return state
        except Exception as ex:
            log("tplink read exception", str(ex))
            return None

    def read(self, addr):
        try:
            (ipAddr, attr) = addr.split(",")
        except ValueError:
            ipAddr = addr
            attr = "relay_state"
        try:
            return int(self.states[ipAddr][attr])
        except TypeError:
            return None

    def write(self, addr, state):
        ipAddr = addr.split(",")[0]
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.connect((ipAddr, port))
            sock_tcp.send(encrypt('{"system":{"set_relay_state":{"state":'+str(state)+'}}}'))
            status = int(json.loads(decrypt(sock_tcp.recv(2048)))["system"]["set_relay_state"]["err_code"])
            sock_tcp.close()
            if status == 0:
                return state
            else:
                return None
        except Exception as ex:
            log("tplink write exception", str(ex))
            return None
