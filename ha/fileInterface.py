from ha.HAClasses import *
import json
import os
import threading
import time

class FileInterface(HAInterface):
    def __init__(self, name, interface=None, event=None, fileName="", readOnly=False):
        HAInterface.__init__(self, name, interface=interface, event=event)
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
        # thread to periodically check for file changes
        def readData():
            if debugFileThread: log(self.name, "readData started")
            while running:
                time.sleep(filePollInterval)
                if  os.stat(self.fileName).st_mtime > self.mtime:
                    self.readData()
        readStatesThread = threading.Thread(target=readData)
        readStatesThread.start()

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
        self.data = json.load(open(self.fileName))
        if self.event:
            self.event.set()

    def writeData(self):
        json.dump(self.data, open(self.fileName, "w"))
        self.mtime = time.time()
        if self.event:
            self.event.set()

