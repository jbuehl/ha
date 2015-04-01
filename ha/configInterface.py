from ha.HAClasses import *
from ha.fileInterface import *

class ConfigInterface(HAInterface):
    def __init__(self, name, interface=None, event=None, fileName="ha.conf"):
        HAInterface.__init__(self, name, interface=interface, event=event)
        try:
            with open(configDir+fileName) as configFile:
                lines = [line.rstrip('\n') for line in configFile]
        except:
            log(self.name, configDir+fileName, "file not found")
            return
        for line in lines:
            if (len(line) > 0) and (line[0] != "#"):
                parts = line.split("=")
                attr = parts[0].rstrip(" ")
                value = parts[1].lstrip(" ")
                try:
                    globals()[attr] = eval(value)
                    debug('debugConf', self.name, attr, "=", value)
                except:
                    log(self.name, "error evaluating", attr, "=", value)
                              
