##################################################################
# configuration
##################################################################

running = True

# Environment
latLong = (34.1486, -118.3965)
tempScale = "F"
webPort = 80

# General debugging
debug = True
debugObject = True
debugState = True
debugThread = True
debugRest = False

# X10 interface
x10Device = "/dev/ttyUSB0"
debugLights = True

# Data base interface
dbRetryInterval = 60
debugSql = False

# AquaLink interface
#aqualinkDevice = "/dev/aqualink"
aqualinkDevice = "/dev/ttyUSB0"
allButtonPanelAddr = '\x09'
monitorMode = False
aqualinkClock = True
debugData = False
debugRaw = False
debugProbe = False
debugAck = False
debugStatus = True
debugAction = True
debugMsg = False
debugTime = True

# Web interface
debugHttp = False
debugWeb = False

# Scheduler
debugEvent = True
debugSched = False

# Pentair interface
#pentairDevice = "/dev/pentair"
pentairDevice = "/dev/ttyUSB1"
pentairAddr = '\x60'
pentairSpeeds = [0, 1200, 1800, 2400, 3200]
debugPentairThread = False
debugPentairData = False

# Solar interface
solarIp = "192.168.1.13:7380"

# Power interface
powerTbl = {"poolCleaner": 1500,
            "poolLight": 491,
            "spaLight": 276,
            "spaBlower": 712}


