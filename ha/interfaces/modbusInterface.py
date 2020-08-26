import minimalmodbus
import time
import threading
from ha import *

minimalmodbus.BAUDRATE = 9600
minimalmodbus.TIMEOUT = 0.5

class ModbusInterface(Interface):
    def __init__(self, name, interface=None, event=None, device="", addr=1):
        Interface.__init__(self, name, interface=interface, event=event)
        self.device = device
        self.addr = addr
        self.instrument = minimalmodbus.Instrument(self.device, self.addr)

    def start(self):
        def readStates():
            debug("debugModbus", "starting readStates")
            while True:
                for sensor in list(self.sensors.values()):
                    debug("debugModbus", "readState", sensor.name)
                    try:
                        self.states[sensor.addr] = self.instrument.read_register(sensor.addr)
                    except Exception as ex:
                        log(self.name, "read exception", sensor.name, sensor.addr, type(ex).__name__, str(ex))
                    time.sleep(1)
                debug("debugModbus", "readStates sleeping")
                time.sleep(60 - len(self.sensors))
        readStateThread = LogThread(name="readStateThread", target=readStates)
        readStateThread.start()

    def read(self, addr):
        return self.states[addr]

    def write(self, addr, value):
        try:
            self.instrument.write_register(sensor.addr, value)
        except Exception as ex:
            log(self.name, "write exception", sensor.name, sensor.addr, type(ex).__name__, str(ex))
