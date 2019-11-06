

from jinja2 import FileSystemLoader
import filelock
from ha import *
from ha.network.environment import *

stateLock = filelock.FileLock(stateDir+stateFileName)

# set the color for the signal strength
def signalColor(signal):
    if signal < -79:
        return "OrangeRed"
    elif signal < -67:
        return "Gold"
    else:
        return "LawnGreen"

# set the color for the ping time
def pingColor(pingTime):
    if pingTime > maxPingTime*1000:
        return "Crimson"
    elif pingTime > 1000:
        return "OrangeRed"
    elif pingTime > 500:
        return "Gold"
    else:
        return "LawnGreen"

def networkUI(order, templates, views):
    # try:
    #     with stateLock.acquire(timeout=5):
    #         (sampleTime, netStats, deviceStats) = json.load(open(stateDir+stateFileName, "r"))
    # except filelock.Timeout:
    #     return "state file locked"
    decoded = False
    while not decoded:
        try:
            (sampleTime, netStats, deviceStats) = json.load(open(stateDir+stateFileName, "r"))
            decoded = True
        except Exception as ex:
            log("exception", str(ex), stateData)
    # add pin time and signal strength colors
    netLines = [[netStat[0]]+[[pingTime, pingColor(pingTime)] for pingTime in netStat[1:4]]+netStat[4:] for netStat in netStats]
    deviceLines = [[tuple(int(x) for x in deviceStat[0].split("."))]+deviceStat[1:4]+ \
                    ([[str(deviceStat[4]), signalColor(deviceStat[4])]] if deviceStat[4] else [["", ""]])+ \
                    deviceStat[5:] for deviceStat in deviceStats]
    netHeads = ["Network", "Router", "Gateway", "Internet", "Download", "Upload"]
    deviceHeads = ["IP address", " ", "MAC address", "Access point", "Sig", "Host name", "Vendor"]
    # determine the sort order for devices
    if order:
        try:
            sortOrder = deviceHeads.index(order)
        except ValueError:
            sortOrder = 0
    else:
        sortOrder = 0
    deviceLines.sort(key = lambda x: x[sortOrder])
    return templates.get_template("network.html").render(title=title, script="", time=sampleTime,
                    netheads=netHeads, netlines=netLines, columnheads=deviceHeads, lines=deviceLines)
