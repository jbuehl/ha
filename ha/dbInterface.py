import MySQLdb
import time
from ha.HAClasses import *
from ha.HAConf import *
from ha.logging import *

class HADbInterface(HAInterface):
    def __init__(self, theName, dataBase, hostName="localhost", userName="", password=""):
        HAInterface.__init__(self, theName, None)
        self.dataBase = dataBase
        self.hostName = hostName
        self.userName = userName
        self.password = password
        self.db = None

    def start(self):
        while not self.db:
            try:
                self.db = MySQLdb.connect(host=self.hostName, user=self.userName, passwd=self.password, db=self.dataBase)
            except:
                log("warning", "Error opening database - retrying in", dbRetryInterval, "seconds")
                time.sleep(dbRetryInterval)

    def read(self, sql):
        if debugSql: log("sql", sql)
        try:
            cur = self.db.cursor()
            if cur.execute(sql) > 0:
                result = cur.fetchall()[0][0]
            else:
                result = "-"
            self.db.commit()
            cur.close()
            return result
        except:
            return "-"

