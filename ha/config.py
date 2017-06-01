# Read configuration files and set global variables

import os
from environment import *
from logging import *

try:
    for configFileName in ['ha.conf']: #os.listdir(configDir):
        debug('debugConf', "config open", configFileName)
        try:
            with open(configDir+configFileName) as configFile:
                configLines = [configLine.rstrip('\n') for configLine in configFile]
            for configLine in configLines:
                if (len(configLine) > 0) and (configLine[0] != "#"):
                    try:
                        debug('debugConf', "config read", configLine)
                        exec(configLine)
                    except:
                        log("config", "error evaluating", configLine)
        except:
            log("config", "error reading", configDir+configFileName)
except:
    log("config", "no config directory", configDir)

