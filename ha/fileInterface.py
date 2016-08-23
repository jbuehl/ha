filePollInterval = 1

from ha.HAClasses import *
import json
import os
import threading
import time

class FileInterface(HAInterface):
    def __init__(self, name, interface=None, event=None, fileName="", readOnly=False, changeMonitor=True):
        HAInterface.__init__(self, name, interface=interface, event=event)
        self.fileName = fileName
        self.readOnly = readOnly
        self.changeMonitor = changeMonitor

    def start(self):
        try:
            # if the file exists, cache the data
            debug('debugFile', self.name, "reading", self.fileName)
            self.readData()
            self.mtime = os.stat(self.fileName).st_mtime
        except:
            # create a new file
            debug('debugFile', self.name, "creating", self.fileName)
            self.data = {}
            self.writeData()
        if self.changeMonitor:
            # thread to periodically check for file changes
            def readData():
                debug('debugFileThread', self.name, "readData started")
                while running:
                    debug('debugFileThread', self.name, "waiting", filePollInterval)
                    time.sleep(filePollInterval)
                    if self.modified():
                        self.readData()
            readStatesThread = threading.Thread(target=readData)
            readStatesThread.start()

    def read(self, addr):
        try:
            # if the file has been modified since it was last read, read it again
            if self.modified():
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

    def modified(self):
        mtime = os.stat(self.fileName).st_mtime
        if mtime > self.mtime:
            debug('debugFile', self.name, "modified", mtime, "last", self.mtime)
            self.mtime = mtime
            return True
        else:
            return False
    
    def readData(self):
        try:
            with open(self.fileName) as dataFile:
                self.data = json.load(dataFile)
        except:
            log(self.name, "readData file read error")
        debug('debugFile', self.name, "readData", self.data)
        if self.event:
            self.event.set()

    def writeData(self):
        debug('debugFile', self.name, "writeData", self.data)
        with open(self.fileName, "w") as dataFile:
            json.dump(self.data, dataFile)
        self.mtime = time.time()
        if self.event:
            self.event.set()

