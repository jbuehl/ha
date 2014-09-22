
from HCClasses import *

class CommandUI(HCUI):
    def __init__(self, theName, theApp, theInterface, theResources):
        HCUI.__init__(self, theName, theApp, theInterface, theResources)

    def start(self):
        self.interface.start()
        while True:
            line = self.interface.readline(None)
            parts = line.split("=")
            name = parts[0].strip().capitalize()
            if name == "List":
                for resource in self.resources.resources.values():
                    print resource.name, ":", resource.getState(), resource.type, resource.interface.name, resource.addr, resource.location
            else:
                try:
                    resource = self.resources.resources[name]
                    if len(parts) > 1:
                        value = eval(parts[1].strip())
                        if not resource.setState(value):
                            print "Unable to set", name
                    print name, "=", resource.getState()
                except KeyError:
                    print "Unknown resource"


