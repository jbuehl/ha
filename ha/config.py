# Read configuration files and set global variables

import os
from environment import *
from logging import *

global debugEnable
debugEnable = False
debugConf = False

try:
    for configFileName in ['ha.conf']: #os.listdir(configDir):
        try:
            with open(configDir+configFileName) as configFile:
                configLines = [configLine.rstrip('\n') for configLine in configFile]
            debugConfOpen = True
            for configLine in configLines:
                if (len(configLine) > 0) and (configLine[0] != "#"):
                    try:
                        (key, value) = configLine.split("=")
                        exec("global "+key)
                        exec(configLine)
                        if debugEnable and debugConf:   # can't use debugging module because of circular references
                            if debugConfOpen:   # log the file open retroactively if debugConf got set
                                log("config open", configFileName)
                                debugConfOpen = False
                            log("config read", configLine)
                    except:
                        log("config", "error evaluating", configLine)
        except:
            log("config", "error reading", configDir+configFileName)
except:
    log("config", "no config directory", configDir)

