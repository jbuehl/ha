# Global variables that define the environment

import os
import socket

# directory structure
rootDir = os.path.expanduser("~")+"/"
configDir = rootDir+"conf/"
keyDir = rootDir+"keys/"
stateDir = rootDir+"state/"
soundDir = rootDir+"sounds/"
dataLogDir = "data/"
dataLogFileName = ""
hostname = socket.gethostname()

# Localization - define these in the config file
    # latLong = (0.0, 0.0)
    # elevation = 0 # elevation in feet
    # tempScale = "F"

# global variables that must be set here
sysLogging = True
