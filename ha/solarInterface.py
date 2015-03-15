from ha.HAClasses import *

class HASolarInterface(HAInterface):
    def __init__(self, theName, theInterface):
        HAInterface.__init__(self, theName, theInterface)
        self.sql = """select %s(%s.%s) from %s,
	            (select date, max(time) time, id from %s
		            where date = curdate()
		            group by id) max
	            where %s.date = max.date and %s.time = max.time and %s.id = max.id;	
	            """

    def read(self, addr):
        try:
            sql = self.sql % (addr[1], addr[0], addr[2], addr[0], addr[0], addr[0], addr[0], addr[0])
            return self.interface.read(sql)
        except:
            return "-"

