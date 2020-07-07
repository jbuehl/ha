dataInterval = 60
block = True

import os
import sys
import time
import subprocess
import threading
import getmac
import json
import requests
import filelock
from ha import *
from ha.network.environment import *

# URL for MAC vendor database
macUrl = "https://code.wireshark.org/review/gitweb?p=wireshark.git;a=blob_plain;f=manuf;hb=HEAD"

# global data
sampleTime = ""
dataLock = threading.Lock()
vendors = {}
stateLock = filelock.FileLock(stateDir+stateFileName)

# these scripts must be stored in the router
"""
/system script
add name=devices owner=admin policy=\
    ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon \
    source=":foreach lease in=[/ip dhcp-server lease find] do={:put \"\
        \$[/ip dhcp-server lease get \$lease address] \
        \$[/ip dhcp-server lease get \$lease mac-address] \
        \$[/ip dhcp-server lease get \$lease host-name]\
    \"}"
add name=static owner=admin policy=\
    ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon \
    source=":foreach static in=[/ip dns static find] do={:put \"\
        \$[/ip dns static get \$static address] \
        \$[/ip dns static get \$static name]\
    \"}"
    """

# these scripts must be stored in each access point
"""
/system script
add name=wlans owner=admin policy=\
    ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon \
    source=":foreach wlan in=[/interface wireless find] do={:put \"\
        \$[/interface wireless get \$wlan name]|\
        \$[/interface wireless get \$wlan band]|\
        \$[/interface wireless get \$wlan frequency]|\
        \$[/interface wireless get \$wlan master-interface]|\
        \$[/interface wireless get \$wlan ssid]\
    \"}"
/system script
add name=clients owner=admin policy=\
    ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon \
    source=":foreach client in=[/interface wireless registration-table find] do={:put \"\
        \$[/interface wireless registration-table get \$client mac-address] \
        \$[/interface wireless registration-table get \$client signal-strength]\
    \"}"
    """
#        \$[/interface wireless registration-table get \$client interface]\

# convert bytes to GB
def bytes2GB(bytes):
    return "%7.3f" % (float(bytes) / 1000000000)

# get MAC vendor database
def getVendors():
    log("getting vendor database from", macUrl)
    while vendors == {}:
        try:
            macReply = requests.get(macUrl)
            for line in macReply.text.split("\n"):
                if (len(line) > 0) and (line[0] != "#"):
                    try:
                        (oui, abbrev, vendor) = line.split("\t")
                        vendors[oui] = vendor
                    except ValueError:
                        pass
        except Exception as ex:
            log("error getting vendors", str(ex))
            time.sleep(10)
    log("got", len(vendors), "vendors")

def getVendor(mac):
    try:
        vendor = vendors[mac[0:8]]
    except KeyError:
        vendor = "unknown"
    return vendor

# get network data
def getNetwork():
    log("Starting network data thread")
    staticScript = "/system script run static"
    leaseScript = "/system script run devices"
    clientScript = "/system script run clients"
    while True:
        try:
            # get static IPs from router
            debug("debugNetwork", "getting static IPs from", router)
            statics = subprocess.check_output("ssh admin@"+router+" "+staticScript, shell=True).decode().split("\r\n")[0:-1]
            # get IP address leases from router
            debug("debugNetwork", "getting leases from", router)
            leases = subprocess.check_output("ssh admin@"+router+" "+leaseScript, shell=True).decode().split("\r\n")[0:-1]
        except subprocess.CalledProcessError:
            log("Router", router, "not responding")

        # get clients and wifi data from each access point
        clientAps = {}
        clientSignals = {}
        for ap in accessPoints:
            debug("debugNetwork", "getting clients from", ap)
            try:
                clients = subprocess.check_output("ssh admin@"+ap+" "+clientScript, shell=True).decode().split("\r\n")[0:-1]
                for client in clients:
                    (mac, signal) = client.split(" ")
                    clientAps[mac] = ap
                    clientSignals[mac] = signal[0:3]
            except subprocess.CalledProcessError:
                log("Access point", ap, "not responding")

        # get ARP table
        debug("debugNetwork", "getting ARPs")
        arpList = subprocess.check_output("arp -na", shell=True).decode().split("\n")[0:-1]
        arps = {}
        for arp in arpList:
            ip = arp.split(" ")[1][1:-1]
            mac = arp.split(" ")[3]
            arps[ip] = mac
        arps[ipAddr] = getmac.get_mac_address(interface=interface)

        # get network statistics
        netstats = {}
        for network in networks.keys():

            # get current ping times
            debug("debugNetwork", "getting ping times for network", network)
            netInterface = networks[network]["interface"]
            routerIp = networks[network]["router"]
            gatewayIp = networks[network]["gateway"]
            internetIp = networks[network]["internet"]
            pingTimes = []
            for hostName in [routerIp, gatewayIp, internetIp]:
                try:
                    pingCmd = "ping -c1 -W"+str(maxPingTime)+" -I "+netInterface+" "+hostName
                    debug("debugNetwork", pingCmd)
                    pingTime = float(subprocess.check_output(pingCmd, shell=True).decode().split("\n")[-2].split()[3].split("/")[0])
                except:
                    pingTime = 999.999
                debug("debugNetwork", hostName, "ping time", pingTime)
                pingTimes.append(pingTime)

            # get throughput statistics
            debug("debugNetwork", "getting throughput stats for network", network)
            try:
                with open(netStatDir+"stats.json") as netStatsFile:
                    stats = json.load(netStatsFile)
                todayStats = stats[network]["daily"][time.strftime("%Y%m%d")]
                inBytes = bytes2GB(todayStats["in"])
                outBytes = bytes2GB(todayStats["out"])
            except:
                inBytes = 0
                outBytes = 0
            netstats[network] = pingTimes+[inBytes, outBytes]

        # create network stats table
        netLines = []
        for network in sorted(netstats.keys()):
            [routerPing, gatewayPing, internetPing, inBytes, outBytes] = netstats[network]
            netLines.append([network, routerPing, gatewayPing, internetPing, inBytes, outBytes])

        # create device stats table
        deviceStats = []

        # static hosts
        for static in statics:
            (ip, hostName) = static.split(" ")
            if hostName not in ignoreHosts:
                try:
                    mac = arps[ip].upper()
                    vendor = getVendor(mac)
                    deviceStats.append([ip, "S", mac, "--wired--", None, hostName, vendor])
                except KeyError:    # ignore hosts that aren't on the network
                    pass

        # DHCP hosts
        for lease in leases:
            leaseItems = lease.split(" ")
            ip = leaseItems[0]
            mac = leaseItems[1]
            hostName = " ".join(leaseItems[2:])
            # hostname aliases
            try:
                hostName = hostAliases[mac]
            except KeyError:
                pass
            if hostName not in ignoreHosts:
                # get wifi signal strength
                try:
                    ap = clientAps[mac]
                    try:
                        signal = int(clientSignals[mac])
                    except ValueError:
                        signal = 0
                except KeyError:
                    # host is known to be wired
                    if hostName in wiredHosts:
                        ap = "--wired--"
                    else:   # host recently disconnected from wifi
                        ap = ""
                    signal = 0
            vendor = getVendor(mac)
            deviceStats.append([ip, "D", mac, ap, signal, hostName, vendor])
            sampleTime = time.strftime("%a %b %d %Y %H:%M")

            # write everything to the state file
            # with stateLock:
            #     json.dump((sampleTime, netLines, deviceStats), open(stateDir+stateFileName, "w"))
            json.dump((sampleTime, netLines, deviceStats), open(stateDir+stateFileName, "w"))
        time.sleep(dataInterval)

if __name__ == "__main__":

    waitForDns()
    # start the thread to get vendor names
    getVendorThread = threading.Thread(target=getVendors)
    getVendorThread.start()

    # start the network data thread
    dataThread = threading.Thread(target=getNetwork)
    dataThread.start()

    # block
    if block:
        while True:
            time.sleep(1)
