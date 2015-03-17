from ha.HAClasses import *
import json
import os
import time

class FileInterface(HAInterface):
    def __init__(self, name, fileName, readOnly=False):
        HAInterface.__init__(self, name, None)
        self.fileName = fileName
        self.readOnly = readOnly

    def start(self):
        try:
            # if the file exists, cache the data
            self.readData()
            self.mtime = os.stat(self.fileName).st_mtime
        except:
            # create a new file
            self.data = {}
            self.writeData()

    def read(self, addr):
        try:
            # if the file has been modified since it was last read, read it again
            if  os.stat(self.fileName).st_mtime > self.mtime:
                self.readData()
            return self.data[addr]
        except:
            return None

    def write(self, addr, value):
        self.data[addr] = value
        if not self.readOnly:
            self.writeData()

    def delete(self, addr):
        del(self.data[addr])
        if not self.readOnly:
            self.writeData()

    def readData(self):
        self.file = open(self.fileName)
        self.data = json.load(self.file)
        self.file.close()

    def writeData(self):
        self.file = open(self.fileName, "w")
        json.dump(self.data, self.file)
        self.file.close()
        self.mtime = time.time()

