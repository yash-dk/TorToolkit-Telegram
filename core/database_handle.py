import psycopg2,os,datetime

from ..functions.pg_plugin import DataBaseHandle
from ..consts.ExecVarsSample import ExecVars
#this will handel the transaction with completed torrents

# this now will handle the setting for the bot
class TorToolkitDB(DataBaseHandle):
    def __init__(self,dburl=None):
        # *** QUERIES ***
        if dburl is None:
            dburl = os.environ.get("DB_URI",None)
            if dburl is None:
                dburl = ExecVars.DB_URI

        super().__init__(dburl)

        settings_schema = """CREATE TABLE IF NOT EXISTS ttk_config (
            id SERIAL PRIMARY KEY NOT NULL,
            var_name VARCHAR(50) NOT NULL UNIQUE,
            var_value VARCHAR(2000) DEFAULT NULL,
            vtype VARCHAR(20) DEFAULT NULL,
            blob_val BYTEA DEFAULT NULL,
            date_changed TIMESTAMP NOT NULL
        )"""

        cur = self._conn.cursor()

        cur.execute(settings_schema)

        self._conn.commit()
        cur.close()

    def set_variable(self,var_name,var_value,update_blob=False,blob_val=None):
        #todo implement blob
        vtype = "str"
        if isinstance(var_value,bool):
            vtype = "bool"
        elif isinstance(var_value,int):
            vtype = "int"

        sql = "SELECT * FROM ttk_config WHERE var_name=%s"
        cur = self.scur()
        
        cur.execute(sql,(var_name,))
        if cur.rowcount > 0:
            sql = "UPDATE ttk_config SET var_value=%s , vtype=%s WHERE var_name=%s"
            cur.execute(sql,(var_value,vtype,var_name))
        else:
            sql = "INSERT INTO ttk_config(var_name,var_value,date_changed,vtype) VALUES(%s,%s,%s,%s)"
            cur.execute(sql,(var_name,var_value,datetime.datetime.now(),vtype))

        self.ccur(cur)
    
    def get_variable(self,var_name):
        sql = "SELECT * FROM ttk_config WHERE var_name=%s"
        cur = self.scur()
        
        cur.execute(sql,(var_name,))
        if cur.rowcount > 0:
            row = cur.fetchone()
            vtype = row[3]
            val = row[2]
            if vtype == "int":
                val = int(row[2])
            elif vtype == "str":
                val = str(row[2])
            elif vtype == "bool":
                if row[2] == "true":
                    val = True
                else:
                    val = False

            return val,row[4]
        else:
            return None,None

        self.ccur(cur)
        

    def __del__(self):
        super().__del__()