from __future__ import print_function
import time
from ha import *

# BMP085 pressure and temp sensor
# Code lifted from Adafruit_BMP085

class BMP085Interface(Interface):

    # Operating Modes
    __BMP085_ULTRALOWPOWER     = 0
    __BMP085_STANDARD          = 1
    __BMP085_HIGHRES           = 2
    __BMP085_ULTRAHIGHRES      = 3

    # BMP085 Registers
    __BMP085_CAL_AC1           = 0xAA  # R   Calibration data (16 bits)
    __BMP085_CAL_AC2           = 0xAC  # R   Calibration data (16 bits)
    __BMP085_CAL_AC3           = 0xAE  # R   Calibration data (16 bits)
    __BMP085_CAL_AC4           = 0xB0  # R   Calibration data (16 bits)
    __BMP085_CAL_AC5           = 0xB2  # R   Calibration data (16 bits)
    __BMP085_CAL_AC6           = 0xB4  # R   Calibration data (16 bits)
    __BMP085_CAL_B1            = 0xB6  # R   Calibration data (16 bits)
    __BMP085_CAL_B2            = 0xB8  # R   Calibration data (16 bits)
    __BMP085_CAL_MB            = 0xBA  # R   Calibration data (16 bits)
    __BMP085_CAL_MC            = 0xBC  # R   Calibration data (16 bits)
    __BMP085_CAL_MD            = 0xBE  # R   Calibration data (16 bits)
    __BMP085_CONTROL           = 0xF4
    __BMP085_TEMPDATA          = 0xF6
    __BMP085_PRESSUREDATA      = 0xF6
    __BMP085_READTEMPCMD       = 0x2E
    __BMP085_READPRESSURECMD   = 0x34

    # Private Fields
    _cal_AC1 = 0
    _cal_AC2 = 0
    _cal_AC3 = 0
    _cal_AC4 = 0
    _cal_AC5 = 0
    _cal_AC6 = 0
    _cal_B1 = 0
    _cal_B2 = 0
    _cal_MB = 0
    _cal_MC = 0
    _cal_MD = 0

    def __init__(self, name, interface, addr=0x77, mode=1, height=0):
        Interface.__init__(self, name, interface)
        correctionAlt = (elevation + height) * 0.3048  # correction height in meters
        self.correction = .68    # fuck it - rough approximation of correction in inches
        self.addr = addr
        # Make sure the specified mode is in the appropriate range
        if ((mode < 0) | (mode > 3)):
          if (self.debug):
            print("Invalid Mode: Using STANDARD by default")
          self.mode = self.__BMP085_STANDARD
        else:
          self.mode = mode
        # Read the calibration data
        self.readCalibrationData()

    def read(self, addr):
        debug('debugTemp', self.name, "read", addr)
        try:
            if addr == "temp":
                return self.readTemperature() * 9 / 5 + 32
            elif addr == "barometer":
                return ((self.readPressure() / 100.0) * 0.0295301) + self.correction
            else:
                return 0
        except:
            return 0

    def readCalibrationData(self):
        # Reads the calibration data from the IC"
        self._cal_AC1 = self.readS16(self.__BMP085_CAL_AC1)   # INT16
        self._cal_AC2 = self.readS16(self.__BMP085_CAL_AC2)   # INT16
        self._cal_AC3 = self.readS16(self.__BMP085_CAL_AC3)   # INT16
        self._cal_AC4 = self.readU16(self.__BMP085_CAL_AC4)   # UINT16
        self._cal_AC5 = self.readU16(self.__BMP085_CAL_AC5)   # UINT16
        self._cal_AC6 = self.readU16(self.__BMP085_CAL_AC6)   # UINT16
        self._cal_B1 = self.readS16(self.__BMP085_CAL_B1)     # INT16
        self._cal_B2 = self.readS16(self.__BMP085_CAL_B2)     # INT16
        self._cal_MB = self.readS16(self.__BMP085_CAL_MB)     # INT16
        self._cal_MC = self.readS16(self.__BMP085_CAL_MC)     # INT16
        self._cal_MD = self.readS16(self.__BMP085_CAL_MD)     # INT16
        self.showCalibrationData()

    def showCalibrationData(self):
        debug("debugBMP085", self.name, "calibration", "AC1 = %6d" % (self._cal_AC1),
                                                       "AC2 = %6d" % (self._cal_AC2),
                                                       "AC3 = %6d" % (self._cal_AC3),
                                                       "AC4 = %6d" % (self._cal_AC4),
                                                       "AC5 = %6d" % (self._cal_AC5),
                                                       "AC6 = %6d" % (self._cal_AC6),
                                                       "B1  = %6d" % (self._cal_B1),
                                                       "B2  = %6d" % (self._cal_B2),
                                                       "MB  = %6d" % (self._cal_MB),
                                                       "MC  = %6d" % (self._cal_MC),
                                                       "MD  = %6d" % (self._cal_MD))

    def readRawTemp(self):
        # Reads the raw (uncompensated) temperature from the sensor
        self.write8(self.__BMP085_CONTROL, self.__BMP085_READTEMPCMD)
        time.sleep(0.005)  # Wait 5ms
        raw = self.readU16(self.__BMP085_TEMPDATA)
        debug("debugBMP085", self.name, "Raw Temp: 0x%04X (%d)" % (raw & 0xFFFF, raw))
        return raw

    def readRawPressure(self):
        # Reads the raw (uncompensated) pressure level from the sensor
        self.write8(self.__BMP085_CONTROL, self.__BMP085_READPRESSURECMD + (self.mode * 2**6))
        if (self.mode == self.__BMP085_ULTRALOWPOWER):
            time.sleep(0.005)
        elif (self.mode == self.__BMP085_HIGHRES):
            time.sleep(0.014)
        elif (self.mode == self.__BMP085_ULTRAHIGHRES):
            time.sleep(0.026)
        else:
            time.sleep(0.008)
        msb = self.readU8(self.__BMP085_PRESSUREDATA)
        lsb = self.readU8(self.__BMP085_PRESSUREDATA+1)
        xlsb = self.readU8(self.__BMP085_PRESSUREDATA+2)
        raw = ((msb * 2**16) + (lsb * 2**8) + xlsb) / 2**(8 - self.mode)
        debug("debugBMP085", self.name, "Raw Pressure: 0x%04X (%d)" % (int(raw) & 0xFFFF, raw))
        return raw

    def readTemperature(self):
        # Gets the compensated temperature in degrees celsius

        # Read raw temp before aligning it with the calibration values
        UT = self.readRawTemp()
        X1 = ((UT - self._cal_AC6) * self._cal_AC5) / 2**15
        X2 = (self._cal_MC * 2**11) / (X1 + self._cal_MD)
        B5 = X1 + X2
        temp = ((B5 + 8) / 2**4) / 10.0
        debug("debugBMP085", self.name, "Calibrated temperature = %f C" % temp)
        return temp

    def readPressure(self):
        # Gets the compensated pressure in pascal
        UT = self.readRawTemp()
        UP = self.readRawPressure()
        self.showCalibrationData()

        # True Temperature Calculations
        X1 = ((UT - self._cal_AC6) * self._cal_AC5) / 2**15
        X2 = (self._cal_MC * 2**11) / (X1 + self._cal_MD)
        B5 = X1 + X2
        debug("debugBMP085", self.name, "X1 = %d" % (X1), "X2 = %d" % (X2), "B5 = %d" % (B5), "True Temperature = %.2f C" % (((B5 + 8) / 2**4) / 10.0))

        # Pressure Calculations
        B6 = B5 - 4000
        X1 = (self._cal_B2 * (B6 * B6) / 2**12) / 2**11
        X2 = (self._cal_AC2 * B6) / 2**11
        X3 = X1 + X2
        B3 = (((self._cal_AC1 * 4 + X3) * 2**self.mode) + 2) / 4
        debug("debugBMP085", self.name, "B6 = %d" % (B6), "X1 = %d" % (X1), "X2 = %d" % (X2), "B3 = %d" % (B3))

        X1 = (self._cal_AC3 * B6) / 2**13
        X2 = (self._cal_B1 * ((B6 * B6) / 2**12)) / 2**16
        X3 = ((X1 + X2) + 2) / 2**2
        B4 = (self._cal_AC4 * (X3 + 32768)) / 2**15
        B7 = (UP - B3) * (50000 / 2**self.mode)
        debug("debugBMP085", self.name, "X1 = %d" % (X1), "X2 = %d" % (X2), "B4 = %d" % (B4), "B7 = %d" % (B7))

        if (B7 < 0x80000000):
          p = (B7 * 2) / B4
        else:
          p = (B7 / B4) * 2

        X1 = (p / 2**8) * (p / 2**8)
        X1 = (X1 * 3038) / 2**16
        X2 = (-7375 * p) / 2**16
        debug("debugBMP085", self.name, "p  = %d" % (p), "X1 = %d" % (X1), "X2 = %d" % (X2))

        p = p + ((X1 + X2 + 3791) / 2**4)
        debug("debugBMP085", self.name, "Pressure = %d Pa" % (p))

        return p

    def readAltitude(self, seaLevelPressure=101325):
        # Calculates the altitude in meters
        altitude = 0.0
        pressure = float(self.readPressure())
        altitude = 44330.0 * (1.0 - pow(pressure / seaLevelPressure, 0.1903))
        debug("debugBMP085", self.name, "Altitude = %d" % (altitude))
        return altitude

    def readU8(self, reg):
        # Read an unsigned byte from the I2C device
        result = self.interface.read((self.addr, reg))
        return result

    def readS8(self, reg):
        # Reads a signed byte from the I2C device
        result = self.interface.read((self.addr, reg))
        if (result > 127):
            return result - 256
        else:
            return result

    def readU16(self, reg):
        # Reads an unsigned 16-bit value from the I2C device
        hibyte = self.interface.read((self.addr, reg))
        result = (hibyte * 2**8) + self.interface.read((self.addr, reg+1))
        return result

    def readS16(self, reg):
        # Reads a signed 16-bit value from the I2C device
        hibyte = self.interface.read((self.addr, reg))
        if (hibyte > 127):
            hibyte -= 256
        result = (hibyte * 2**8) + self.interface.read((self.addr, reg+1))
        return result

    def write8(self, reg, value):
        # Writes an 8-bit value to the specified register/address
        self.interface.write((self.addr, reg), value)
