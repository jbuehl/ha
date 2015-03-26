##################################################################
# configuration
##################################################################

running = True

# Environment
latLong = (34.1486, -118.3965)
tempScale = "F"
rootDir = "/root/"
keyDir = rootDir+"keys/"
stateDir = rootDir+"state/"
smsSid = keyDir+"twilio.sid"
smsToken = keyDir+"twilio.tkn"
notifyFromNumber = keyDir+"notifyFromNumber"

# General debugging
debug = True
debugObject = True
debugState = True
debugStateChange = False
debugThread = True
debugInterrupt = False
sysLogging = True

# X10 interface
x10Device = "/dev/ttyUSB0"
debugLights = True

# I2C and GPIO interfaces
debugI2C = False
debugGPIO = False

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
debugTime = False

# spa interface
spaTempTarget = 100
spaReadyNotifyNumbers = keyDir+"spaReadyNotifyNumbers"
debugSpaLight = True

# Shades interface
debugShades = False

# REST interface
debugRest = False
debugRestResources = False
debugRestGet = False
debugRestPut = False
debugRestStates = True

# Web interface
webPort = 80
webRestPort = 7478
webUpdateInterval = 1
webUpdateStateChange = True
webLogging = False
debugHttp = False
debugWeb = True

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

# File interface
debugFileThread = True
filePollInterval = 10

# Solar interface
solarIp = "192.168.1.13:7380"
solarFileName = "/root/solar.json"

# Loads interface
loadFileName = "/root/power.json"

# Power interface
powerTbl = {"poolCleaner": 1500,
            "poolLight": 491,
            "spaLight": 276,
            "spaBlower": 712}


