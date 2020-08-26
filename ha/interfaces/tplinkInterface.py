tcpTimeout = 10.0
stateInterval = 1

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
            debug("debugTplink", "tplink", "getStates starting")
            while True:
                for sensor in list(self.sensors.values()):
                    try:
                        (ipAddr, attr) = sensor.addr.split(",")
                    except ValueError: # ignore sensors with an attribute so devices are only polled once
                        ipAddr = sensor.addr.split(",")[0]
                        state = self.readState(ipAddr)
                        if state != self.states[ipAddr]:
                            if state and self.states[ipAddr]:
                                if state["relay_state"] != self.states[ipAddr]["relay_state"]:
                                    debug("debugTplink", sensor.name, "state:", state["relay_state"], "rssi:", state["rssi"])
                            self.states[ipAddr] = state
                            sensor.notify()
                    except Exception as ex:
                        log("tplink state exception", self.sensorAddrs[ipAddr].name, ipAddr, type(ex).__name__, str(ex))
                time.sleep(stateInterval)
            debug("debugTplink", "tplink", "getStates terminated")
        stateThread = LogThread(name="stateThread", target=getStates)
        stateThread.start()

    def readState(self, ipAddr):
        debug("debugTplink", "tplink", "readState", ipAddr)
        try:
            tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSocket.connect((ipAddr, port))
            tcpSocket.settimeout(tcpTimeout)
            tcpSocket.send(encrypt('{"system":{"get_sysinfo":{}}}'))
            state = json.loads(decrypt(tcpSocket.recv(2048)))["system"]["get_sysinfo"]
            tcpSocket.close()
            return state
        except Exception as ex:
            log("tplink read exception", self.sensorAddrs[ipAddr].name, ipAddr, type(ex).__name__, str(ex))
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
        # only relay_state can be written
        ipAddr = addr.split(",")[0]
        try:
            tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSocket.connect((ipAddr, port))
            tcpSocket.settimeout(tcpTimeout)
            tcpSocket.send(encrypt('{"system":{"set_relay_state":{"state":'+str(state)+'}}}'))
            status = int(json.loads(decrypt(tcpSocket.recv(2048)))["system"]["set_relay_state"]["err_code"])
            tcpSocket.close()
            if status == 0:
                # update the cached state
                self.states[ipAddr]["relay_state"] = state
                self.sensorAddrs[ipAddr].notify()
                return state
            else:
                return None
        except Exception as ex:
            log("tplink write exception", self.sensorAddrs[ipAddr].name, ipAddr, type(ex).__name__, str(ex))
            return None
