##################################################################
# configuration
##################################################################

running = True

# Environment
rootDir = "/root/"
configDir = rootDir+"conf/"
keyDir = rootDir+"keys/"
stateDir = rootDir+"state/"
sysLogging = True

# Localization
latLong = (34.1486, -118.3965)
elevation = 620 # elevation in feet
tempScale = "F"

# Notification
smsSid = keyDir+"twilio.sid"
smsToken = keyDir+"twilio.tkn"
notifyFromNumber = keyDir+"notifyFromNumber"

# General debugging
debugEnable = False
debugConf = False
debugObject = False
debugState = False
debugStateChange = False
debugThread = False
debugInterrupt = False

# REST interface
debugRest = False
debugRestResources = False
debugRestGet = False
debugRestPut = False
debugRestStates = False

# Scheduler
debugEvent = False
debugSched = False

