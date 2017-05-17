##################################################################
# configuration
##################################################################

import os

running = True

# Environment
rootDir = os.path.dirname(os.path.realpath(__file__))+"/../../"
configDir = rootDir+"conf/"
keyDir = rootDir+"keys/"
stateDir = rootDir+"state/"
sysLogging = True

# Localization
latLong = (34.149044, -118.401994)
elevation = 620 # elevation in feet
tempScale = "F"

