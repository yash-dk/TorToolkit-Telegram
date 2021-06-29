from .mongo_db import MongoDB
from ..consts.ExecVarsSample import ExecVars
import os,datetime, json

class TorToolkitDB(MongoDB):
    def __init__(self,dburl=None):
        # *** QUERIES ***
        if dburl is None:
            dburl = os.environ.get("DB_URI",None)
            if dburl is None:
                dburl = ExecVars.DB_URI

        super().__init__(dburl)

        

    def set_variable(self,var_name,var_value,update_blob=False,blob_val=None):
        #todo implement blob - done
        # remember to handle the memoryview
        db = self._db
        config = db.ttk_config

        vtype = "str"
        if isinstance(var_value,bool):
            vtype = "bool"
        elif isinstance(var_value,int):
            vtype = "int"
        
        if update_blob:
            vtype = "blob"

        res = config.find({"var_name":var_name})
        if res.count() > 0:
            if update_blob:
                var_value = blob_val
            vardoc = res[0]
            config.update({"_id": vardoc["_id"]}, {"$set":{"var_value":var_value}})
        else:
            if update_blob:
                var_value = blob_val
            data = {"var_name":var_name, "var_value":var_value, "var_type": vtype}
            config.insert_one(data)



    
    def get_variable(self,var_name):
        db = self._db
        config = db.ttk_config
        res = config.find({"var_name":var_name})
        
        
        if res.count() > 0:
            row = res[0]
            vtype = row["var_type"]
            val = row["var_value"]
            if vtype == "int":
                val = int(val)
            elif vtype == "str":
                val = str(val)
            elif vtype == "bool":
                if val == "true":
                    val = True
                else:
                    val = False
            
            if vtype == "blob":
                return None, val
            else:
                return val,None
        else:
            return None,None

        
class UserDB(MongoDB):
    shared_users = {}
    def __init__(self,dburl=None):
        if dburl is None:
            dburl = os.environ.get("DB_URI",None)
            if dburl is None:
                dburl = ExecVars.DB_URI

        super().__init__(dburl)

    def get_variable(self, var, user_id):
        user_id = str(user_id)
        db = self._db
        users = db.ttk_users
        
        # search the cache
        

        
        res = users.find({"user_id":user_id})

        if res.count() > 0:
            user = res[0]
            jdata = user["json_data"]
            jdata = json.loads(jdata)
            #self.shared_users[user_id] = jdata
            return jdata.get(var)
        else:
            return None
            

    def set_variable(self, var, value, user_id):
        user_id = str(user_id)
        db = self._db
        users = db.ttk_users
        # implement cache later.
        

        res = users.find({"user_id":user_id})

        if res.count() > 0:
            user = res[0]
            jdata = user["json_data"]
            jdata = json.loads(jdata)
            jdata[var] = value
            #self.shared_users[user_id] = jdata
        else:
            ...
            #self.shared_users[user_id] = {var:value}

        
        if res.count() > 0:
            user = res[0]
            users.update({"_id":user["_id"]}, {"$set":{"json_data":json.dumps(jdata)}})

        else:
            jdata = {var:value}
            users.insert_one({"user_id":user_id, "json_data":json.dumps(jdata)})
        
    def get_rclone(self, user_id):
        user_id = str(user_id)
        db = self._db
        users = db.ttk_users

        res = users.find({"user_id":user_id})
        
        if res.count() > 0:
            row = res[0]

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
        db = self._db
        users = db.ttk_users

        res = users.find({"user_id":user_id})
        
        
        if res.count() > 0:
            row = res[0]
            
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
        db = self._db
        users = db.ttk_users

        res = users.find({"user_id":user_id})
        
        if isinstance(rclonefile, str):
            with open(rclonefile, "rb") as f:
                rclonefile = f.read()

        if res.count() > 0:
            users.update({"user_id":user_id}, {"$set":{"rclone_file": rclonefile}})
        else:
            users.insert_one({"user_id":user_id, "rclone_file": rclonefile})

        return True

    def set_thumbnail(self, thumbnail, user_id):
        user_id = str(user_id)
        db = self._db
        users = db.ttk_users

        res = users.find({"user_id":user_id})
        
        if isinstance(thumbnail, str):
            with open(thumbnail, "rb") as f:
                thumbnail = f.read()

        if res.count() > 0:
            users.update({"user_id":user_id}, {"$set":{"thumbnail": thumbnail}})
        else:
            users.insert_one({"user_id":user_id, "thumbnail": thumbnail})

        return True

class TtkTorrents(MongoDB):
    def __init__(self,dburl=None):
        if dburl is None:
            dburl = os.environ.get("DB_URI",None)
            if dburl is None:
                dburl = ExecVars.DB_URI

        super().__init__(dburl)
        

    def add_torrent(self,hash_id,passw):
        db = self._db
        tors = db.ttk_torrents

        res = tors.find({"hash_id":hash_id})

        if res.count() > 0:
            tors.update({"hash_id":hash_id},{"$set":{"passw":passw}})
        else:
            tors.insert_one({"hash_id":hash_id, "passw":passw, "enab":True})
        
    def disable_torrent(self,hash_id):
        db = self._db
        tors = db.ttk_torrents

        res = tors.find({"hash_id":hash_id})
        
        if res.count() > 0:
            tors.update({"hash_id":hash_id},{"$set": {"enab": False}})
        
        
    def get_password(self,hash_id):
        db = self._db
        tors = db.ttk_torrents

        res = tors.find({"hash_id":hash_id})

        if res.count() > 0:
            row = res[0]
            return row["passw"]
        else:
            return False

    def purge_all_torrents(self):
        db = self._db
        tors = db.ttk_torrents

        tors.delete_many({})