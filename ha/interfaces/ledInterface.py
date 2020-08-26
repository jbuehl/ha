flickerFreq = 100   # frequency of flickering per second

import random
import time
import threading
from ha import *

class LedInterface(Interface):
    def __init__(self, name, interface=None, event=None):
        Interface.__init__(self, name, interface=interface, event=event)
        self.running = False
        self.states = {}

    def read(self, addr):
        debug('debugLed', self.name, "read", addr)
        return self.states[addr]

    def write(self, addr, value):
        debug('debugLed', self.name, "write", addr, value)
        self.states[addr] = value
        def flickerThread():
            debug('debugLed', self.name, "starting", addr, value)
            while self.running:
               self.interface.write(addr, 1)
               time.sleep(random.random()/flickerFreq) 
               self.interface.write(addr, 0)
               time.sleep(random.random()/flickerFreq) 
            debug('debugLed', self.name, "ending", addr, value)
        if (value == 0) or (value == 1):
            if self.running:
                self.running = False
                time.sleep(2./flickerFreq)  # wait for thread to finish
            self.interface.write(addr, value)
        elif value == 2:
            self.thread = LogThread(name="self.thread", target=flickerThread)
            self.running = True
            self.thread.start()    


