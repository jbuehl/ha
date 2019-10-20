filePollInterval = 1

from ha import *
import json
import os
import threading
import time

class FileInterface(Interface):
    def __init__(self, name, interface=None, event=None, fileName="", readOnly=False, changeMonitor=True, defaultValue=None, initialState={}):
        Interface.__init__(self, name, interface=interface, event=event)
        self.fileName = fileName
        self.readOnly = readOnly
        self.changeMonitor = changeMonitor
        self.defaultValue = defaultValue
        self.initialState = initialState
        self.data = {}
        self.mtime = 0
        self.lock = threading.Lock()

    def start(self):
        try:
            # if the file exists, cache the data
            debug('debugFile', self.name, "reading", self.fileName)
            self.readData()
            self.mtime = os.stat(self.fileName).st_mtime
        except:
            # create a new file
            debug('debugFile', self.name, "creating", self.fileName)
            self.data = self.initialState
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
        with self.lock:
            try:
                value = self.data[addr]
            except KeyError:
                value = self.defaultValue
        debug('debugFile', self.name, "read", "addr", addr, "value", value)
        return value

    def write(self, addr, value):
        if not self.readOnly:
            debug('debugFile', self.name, "write", "addr", addr, "value", value)
            with self.lock:
                self.data[addr] = value
            self.notify()
            self.writeData()

    def delete(self, addr):
        if not self.readOnly:
            with self.lock:
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
            jsonData = ""
            while jsonData == "":
                with open(self.fileName) as dataFile:
                    with self.lock:
                        jsonData = dataFile.read()
            self.data = json.loads(jsonData)
        except Exception as ex:
            log(self.name, self.fileName, "readData file read error", str(ex), "jsonData", str(jsonData))
        debug('debugFile', self.name, "readData", self.data)

    def writeData(self):
        debug('debugFile', self.name, "writeData", self.data)
        with open(self.fileName, "w") as dataFile:
            with self.lock:
                json.dump(self.data, dataFile)
        self.mtime = time.time()
