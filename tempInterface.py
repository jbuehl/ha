# MCP9803 temp sensor

class TempInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)

    def read(self, theAddr):
        try:
            temp = self.interface.readWord(theAddr, 0x00)
            # assume 9 bit resolution
            tempC = float(((temp&0x00ff)<<1) | ((temp&0x8000)>>15)) * .5
            return tempC
        except:
            return 0

