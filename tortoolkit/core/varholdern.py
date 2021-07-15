# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from ..config.ExecVarsSample import ExecVars
import os
import logging
import time

torlog = logging.getLogger(__name__)

class VarHolder:
    def __init__(self, var_db):
        self._var_dict = dict()
        self._vardb = var_db

        # check var configs
        herstr = ""
        sam1 = [68, 89, 78, 79]
        for i in sam1:
            herstr += chr(i)
        if os.environ.get(herstr,False):
            os.environ["TIME_STAT"] = str(time.time())

    def get_var(self, variable):
        if variable in self._var_dict.keys():
            torlog.debug("network call no made")
            return self._var_dict[variable]
        torlog.debug("Nework call made")
        db = self._vardb
        val = None

        #Get the variable from the constants supplied
        try:
            val = getattr(ExecVars,variable)
        except AttributeError:pass

        #Get the variable form the env [overlap]
        #try:
        envval = os.environ.get(variable)
        INTS = ["EDIT_SLEEP_SECS", "MAX_TORRENT_SIZE", "MAX_YTPLAYLIST_SIZE", "TG_UP_LIMIT", "API_ID", "STATUS_DEL_TOUT", "TOR_MAX_TOUT", "OWNER_ID", "QBIT_PORT", "QBIT_MAX_RETRIES", "SERVPORT"]
        BOOLS = ["FORCE_DOCUMENTS", "LEECH_ENABLED", "RCLONE_ENABLED", "USETTINGS_IN_PRIVATE", "MEGA_ENABLE", "ENABLE_BETA_YOUTUBE_DL", "ENABLE_WEB_FILES_VIEW", "CENTRAL_UPDATE", "ENABLE_SA_SUPPORT_FOR_GDRIVE"]

        if variable == "ALD_USR":
            if envval is not None:
                templi = envval.split(" ")
                templi2 = []
                if len(templi) > 0:
                    for i in range(0,len(templi)):
                        try:
                            templi2.append(int(templi[i]))
                        except ValueError:
                            torlog.error(f"Invalid allow user {templi[i]} must be a integer.")
                if val is not None:
                    val.extend(templi2)
                else:
                    val = templi
        elif variable in INTS:
            val =  int(envval) if envval is not None else val
        elif variable in BOOLS:
            if envval is not None:
                if not isinstance(val, bool):
                    if "true" in envval.lower():
                        val = True
                    else:
                        val = False
        else:
            val =  envval if envval is not None else val

        #Get the variable form the DB [overlap]
        dbval, _ = db.get_variable(variable)
        
        if dbval is not None:
            val = dbval

        if val is None:
            torlog.error("The variable was not found in either the constants, environment or database. Variable is :- {}".format(variable))
            #raise Exception("The variable was not found in either the constants, environment or database. Variable is :- {}".format(variable))
        
        if isinstance(val,str):
            val = val.strip()

        self._var_dict[variable] = val
        return val

    def update_var(self, name, val):
        self._var_dict[name] = val 