import socket
import json
import struct
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
    def __init__(self, name, interface=None):
        Interface.__init__(self, name, interface)

    def read(self, addr):
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.connect((addr, port))
            sock_tcp.send(encrypt('{"system":{"get_sysinfo":{}}}'))
            state = int(json.loads(decrypt(sock_tcp.recv(2048)))["system"]["get_sysinfo"]["relay_state"])
            sock_tcp.close()
            return state
        except Exception as ex:
            log("tplink read exception", str(ex))
            return None

    def write(self, addr, state):
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.connect((addr, port))
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
