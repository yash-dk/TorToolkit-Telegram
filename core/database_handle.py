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

class TtkUpload(DataBaseHandle):
    def __init__(self,dburl=None):
        # *** QUERIES ***
        if dburl is None:
            dburl = os.environ.get("DB_URI",None)
            if dburl is None:
                dburl = ExecVars.DB_URI

        super().__init__(dburl)

        uploads_schema = """CREATE TABLE IF NOT EXISTS ttk_uploads (
            id SERIAL PRIMARY KEY NOT NULL,
            chat_id VARCHAR(30), --Moslty Overkill
            message_id VARCHAR(30), --Moslty Overkill
            cancel BOOLEAN DEFAULT false,
            is_batch BOOLEAN DEFAULT false
        )"""

        cur = self._conn.cursor()

        cur.execute(uploads_schema)

        self._conn.commit()
        cur.close()

    def register_upload(self,chat_id,mes_id,is_batch=False):
        chat_id = str(chat_id)
        mes_id = str(mes_id)

        cur = self.scur()
        sql = "SELECT * FROM ttk_uploads WHERE chat_id=%s and message_id=%s"
        
        cur.execute(sql,(chat_id,mes_id))

        if cur.rowcount > 0:
            row = cur.fetchone()
            sql = "DELETE FROM ttk_uploads WHERE id=%s"
            cur.execute(sql,(row[0],))

        sql = "INSERT INTO ttk_uploads(chat_id,message_id,is_batch) VALUES(%s,%s,%s)"
        
        cur.execute(sql,(chat_id,mes_id,is_batch))
        self.ccur(cur)

    def cancel_download(self,chat_id,mes_id):
        chat_id = str(chat_id)
        mes_id = str(mes_id)

        cur = self.scur()
        sql = "SELECT * FROM ttk_uploads WHERE chat_id=%s and message_id=%s"
        
        cur.execute(sql,(chat_id,mes_id))

        if cur.rowcount == 0:
            self.ccur(cur)
            return False
        else:
            sql = "UPDATE ttk_uploads SET cancel=TRUE WHERE chat_id=%s and message_id=%s"
            cur.execute(sql,(chat_id,mes_id))
            self.ccur(cur)
            return True

    def get_cancel_status(self,chat_id,mes_id):
        chat_id = str(chat_id)
        mes_id = str(mes_id)

        cur = self.scur()
        sql = "SELECT * FROM ttk_uploads WHERE chat_id=%s and message_id=%s"
        
        cur.execute(sql,(chat_id,mes_id))

        if cur.rowcount == 0:
            self.ccur(cur)
            return False
        else:
            row = cur.fetchone()
            cancel = row[3]
            self.ccur(cur)
            return cancel


    def deregister_upload(self,chat_id,mes_id):
        chat_id = str(chat_id)
        mes_id = str(mes_id)
        
        sql = "DELETE FROM ttk_uploads WHERE chat_id=%s and message_id=%s"
        cur = self.scur()
        cur.execute(sql,(chat_id,mes_id))
        self.ccur(cur)


    def __del__(self):
        super().__del__()