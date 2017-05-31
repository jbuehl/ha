from logging import *

# read configuration files
try:
    for configFileName in ['ha.conf']: #os.listdir(configDir):
        debug('debugConf', "config open", configFileName)
        try:
            with open(configDir+configFileName) as configFile:
                configLines = [configLine.rstrip('\n') for configLine in configFile]
            for configLine in configLines:
                if (len(configLine) > 0) and (configLine[0] != "#"):
                    try:
                        exec(configLine)
                        debug('debugConf', "config read", configLine)
                    except:
                        log("config", "error evaluating", configLine)
        except:
            log("config", "error reading", configDir+configFileName)
except:
    log("config", "no config directory", configDir)

