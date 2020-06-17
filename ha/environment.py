# Global variables that define the environment

import os
import socket

# directory structure
rootDir = os.path.dirname(os.path.realpath(__file__))+"/../../"
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
    # metricsServer = "metrics.example.com"

# global variables that must be set here
sysLogging = True
