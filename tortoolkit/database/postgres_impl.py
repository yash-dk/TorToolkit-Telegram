# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import psycopg2,os,datetime
import psycopg2.extras
from .postrgres_db import PostgresDB
from ..consts.ExecVarsSample import ExecVars
import json
from typing import BinaryIO, Union
#this will handel the transaction with completed torrents

# this now will handle the setting for the bot
class TorToolkitDB(PostgresDB):
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

        cur = self.scur()
        try:
            # Sometimes multiple instance try to creat which may cause this error
            cur.execute(settings_schema)
        except psycopg2.errors.UniqueViolation: # pylint: disable=no-member
            pass
        
        self._conn.commit()
        self.ccur(cur)

    def set_variable(self,var_name,var_value,update_blob=False,blob_val=None):
        #todo implement blob - done
        # remember to handle the memoryview
        vtype = "str"
        if isinstance(var_value,bool):
            vtype = "bool"
        elif isinstance(var_value,int):
            vtype = "int"
        
        if update_blob:
            vtype = "blob"

        sql = "SELECT * FROM ttk_config WHERE var_name=%s"
        cur = self.scur()
        
        cur.execute(sql,(var_name,))
        if cur.rowcount > 0:
            if not update_blob:
                sql = "UPDATE ttk_config SET var_value=%s , vtype=%s WHERE var_name=%s"
            else:
                sql = "UPDATE ttk_config SET blob_val=%s , vtype=%s WHERE var_name=%s"
                var_value = blob_val

            cur.execute(sql,(var_value,vtype,var_name))
        else:
            if not update_blob:
                sql = "INSERT INTO ttk_config(var_name,var_value,date_changed,vtype) VALUES(%s,%s,%s,%s)"
            else:
                sql = "INSERT INTO ttk_config(var_name,blob_val,date_changed,vtype) VALUES(%s,%s,%s,%s)"
                var_value = blob_val
            
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


class UserDB(PostgresDB):
    shared_users = {}
    def __init__(self,dburl=None):
        if dburl is None:
            dburl = os.environ.get("DB_URI",None)
            if dburl is None:
                dburl = ExecVars.DB_URI

        super().__init__(dburl)
        cur = self.scur()
        table = """CREATE TABLE IF NOT EXISTS ttk_users(
            id SERIAL PRIMARY KEY NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            json_data VARCHAR(1000) NOT NULL, --Keeping it as json so that it flexible to add stuff.
            rclone_file BYTEA DEFAULT NULL,
            thumbnail BYTEA DEFAULT NULL
        )
        """

        try:
            # Sometimes multiple instance try to creat which may cause this error
            cur.execute(table)
        except psycopg2.errors.UniqueViolation: # pylint: disable=no-member
            pass
        
        self.ccur(cur)

    def get_variable(self, var, user_id):
        user_id = str(user_id)
        sql = "SELECT * FROM ttk_users WHERE user_id=%s"
        # search the cache
        user = self.shared_users.get(user_id)
        if user is not None:
            return user.get(var)
        else:
            cur = self.scur(dictcur=True)
            
            cur.execute(sql, (user_id,))
            if cur.rowcount > 0:
                user = cur.fetchone()
                jdata = user.get("json_data")
                jdata = json.loads(jdata)
                self.shared_users[user_id] = jdata
                return jdata.get(var)
            else:
                return None
                

            self.ccur(cur)

    def set_variable(self, var, value, user_id):
        user_id = str(user_id)
        sql = "SELECT * FROM ttk_users WHERE user_id=%s"
        # search the cache
        cur = self.scur(dictcur=True)

        user = self.shared_users.get(user_id)
        if user is not None:
            self.shared_users[user_id][var] = value
             
        else:
            
            cur.execute(sql, (user_id,))
            if cur.rowcount > 0:
                user = cur.fetchone()
                jdata = user.get("json_data")
                jdata = json.loads(jdata)
                jdata[var] = value
                self.shared_users[user_id] = jdata
            else:
                self.shared_users[user_id] = {var:value}

        cur.execute(sql, (user_id,))
        if cur.rowcount > 0:
            insql = "UPDATE ttk_users SET json_data = %s where user_id=%s"
            cur.execute(insql, ( json.dumps(self.shared_users.get(user_id)), user_id))

        else:
            insql = "INSERT INTO ttk_users(user_id, json_data) VALUES(%s, %s)"
            cur.execute(insql, (user_id, json.dumps(self.shared_users.get(user_id))))
        
        self.ccur(cur)

    def get_rclone(self, user_id):
        user_id = str(user_id)
        sql = "SELECT * FROM ttk_users WHERE user_id=%s"
        cur = self.scur(dictcur=True)

        cur.execute(sql, (user_id,))
        
        if cur.rowcount > 0:
            row = cur.fetchone()
            self.ccur(cur)

            if row["rclone_file"] is None:
                return False
            else:
                path = os.path.join(os.getcwd(), 'userdata')
                if not os.path.exists(path):
                    os.mkdir(path)
                
                path = os.path.join(path, user_id)
                if not os.path.exists(path):
                    os.mkdir(path)
                
                path = os.path.join(path, "rclone.conf")
                with open(path, "wb") as rfile:
                    rfile.write(row["rclone_file"])
                
                return path
        else:
            return False


    def get_thumbnail(self, user_id):
        user_id = str(user_id)
        sql = "SELECT * FROM ttk_users WHERE user_id=%s"
        cur = self.scur(dictcur=True)

        cur.execute(sql, (user_id,))
        
        
        if cur.rowcount > 0:
            row = cur.fetchone()
            self.ccur(cur)
            if row["thumbnail"] is None:
                return False
            else:
                path = os.path.join(os.getcwd(), 'userdata')
                if not os.path.exists(path):
                    os.mkdir(path)
                
                path = os.path.join(path, user_id)
                if not os.path.exists(path):
                    os.mkdir(path)
                
                path = os.path.join(path, "thumbnail.jpg")
                with open(path, "wb") as rfile:
                    rfile.write(row["thumbnail"])
                
                return path
        else:
            return False

    def set_rclone(self, rclonefile, user_id):
        user_id = str(user_id)

        sql = "SELECT * FROM ttk_users WHERE user_id=%s"
        cur = self.scur(dictcur=True)

        cur.execute(sql, (user_id,))
        if cur.rowcount > 0:
            insql = "UPDATE ttk_users SET rclone_file=%s WHERE user_id=%s"
            cur.execute(insql, (rclonefile, user_id))

        else:
            insql = "INSERT INTO ttk_users(user_id, json_data, rclone_file) VALUES(%s, '{}', %s)"
            cur.execute(insql, (user_id, rclonefile))

        self.ccur(cur)
        return True

    def set_thumbnail(self, thumbnail, user_id):
        user_id = str(user_id)

        sql = "SELECT * FROM ttk_users WHERE user_id=%s"
        cur = self.scur(dictcur=True)

        cur.execute(sql, (user_id,))
        if cur.rowcount > 0:
            insql = "UPDATE ttk_users SET thumbnail=%s WHERE user_id=%s"
            cur.execute(insql, (thumbnail, user_id))

        else:
            insql = "INSERT INTO ttk_users(user_id, json_data, thumbnail) VALUES(%s, '{}', %s)"
            cur.execute(insql, (user_id, thumbnail))

        self.ccur(cur)
        return True

class TtkTorrents(PostgresDB):
    def __init__(self,dburl=None):
        if dburl is None:
            dburl = os.environ.get("DB_URI",None)
            if dburl is None:
                dburl = ExecVars.DB_URI

        super().__init__(dburl)
        cur = self.scur()
        table = """CREATE TABLE IF NOT EXISTS ttk_torrents(
            id SERIAL PRIMARY KEY NOT NULL,
            hash_id VARCHAR(100) NOT NULL,
            passw VARCHAR(10) NOT NULL,
            enab BOOLEAN DEFAULT true
        )
        """

        try:
            # Sometimes multiple instance try to creat which may cause this error
            cur.execute(table)
        except psycopg2.errors.UniqueViolation: # pylint: disable=no-member
            pass
        
        self.ccur(cur)

    def add_torrent(self,hash_id,passw):
        sql = "SELECT * FROM ttk_torrents WHERE hash_id=%s"
        cur = self.scur()
        cur.execute(sql,(hash_id,))
        if cur.rowcount > 0:
            sql = "UPDATE ttk_torrents SET passw=%s WHERE hash_id=%s"
            cur.execute(sql,(passw,hash_id))
        else:
            sql = "INSERT INTO ttk_torrents(hash_id,passw) VALUES(%s,%s)"
            cur.execute(sql,(hash_id,passw))
        
        self.ccur(cur)

    def disable_torrent(self,hash_id):
        sql = "SELECT * FROM ttk_torrents WHERE hash_id=%s"
        cur = self.scur()
        cur.execute(sql,(hash_id,))
        if cur.rowcount > 0:
            sql = "UPDATE ttk_torrents SET enab=false WHERE hash_id=%s"
            cur.execute(sql,(hash_id,))

        self.ccur(cur)
        
    def get_password(self,hash_id):
        sql = "SELECT * FROM ttk_torrents WHERE hash_id=%s"
        cur = self.scur()
        cur.execute(sql,(hash_id,))
        if cur.rowcount > 0:
            row = cur.fetchone()
            self.ccur(cur)
            return row[2]
        else:
            self.ccur(cur)
            return False

    def purge_all_torrents(self):
        sql = "DELETE FROM ttk_torrents"
        cur = self.scur()
        cur.execute(sql)
        self.ccur(cur)

    def get_variable(self, var_name: str) -> Union[str, int, list, BinaryIO]:
        pass

    def set_variable(self, var_name: str, var_value: Union[list, str, int], update_blob: bool, blob_value: BinaryIO) -> None:
        pass