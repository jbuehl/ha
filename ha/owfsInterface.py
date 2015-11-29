from ha.HAClasses import *

# One Wire File System interface

class OWFSInterface(HAInterface):
    def __init__(self, name, interface=None, home="/mnt/1wire/", event=None):
        HAInterface.__init__(self, name, interface, event=event)
        self.home = home

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        try:
            with open(self.home+addr+"/temperature") as owfs:
                value = owfs.read()
                try:
                    return int(float(value)+.5)
                except:
                    return value
        except:
            return 0

