# Global variables that define the environment

import os

# directory structure
rootDir = os.path.dirname(os.path.realpath(__file__))+"/../../"
configDir = rootDir+"conf/"
keyDir = rootDir+"keys/"
stateDir = rootDir+"state/"
soundDir = rootDir+"sounds/"
dataLogDir = "data/"
dataLogFileName = ""

# Localization - FIXME - put in a config file
latLong = (34.149044, -118.401994)
elevation = 620 # elevation in feet
tempScale = "F"

# global variables that must be set here
sysLogging = True

