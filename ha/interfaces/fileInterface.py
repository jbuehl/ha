filePollInterval = 1

from ha import *
import json
import os
import threading
import time

class FileInterface(Interface):
    objectArgs = ["interface", "event"]
    def __init__(self, name, interface=None, event=None, fileName="", readOnly=False, changeMonitor=True, defaultValue=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.fileName = fileName
        self.readOnly = readOnly
        self.changeMonitor = changeMonitor
        self.defaultValue = defaultValue

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
                        self.notify()
            readStatesThread = threading.Thread(target=readData)
            readStatesThread.start()

    def read(self, addr):
        try:
            return self.data[addr]
        except KeyError:
            return self.defaultValue

    def write(self, addr, value):
        if not self.readOnly:
            self.data[addr] = value
            self.notify()
            self.writeData()

    def delete(self, addr):
        if not self.readOnly:
            del(self.data[addr])
            self.notify()
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
            log(self.name, self.fileName, "readData file read error")
        debug('debugFile', self.name, "readData", self.data)

    def writeData(self):
        debug('debugFile', self.name, "writeData", self.data)
        with open(self.fileName, "w") as dataFile:
            json.dump(self.data, dataFile)
        self.mtime = time.time()
