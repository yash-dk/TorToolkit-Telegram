#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = "2.0.2.alpha"
__author__ = "YashDK Github@yash-dk"
#
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(),logging.FileHandler("torlog.txt")]
)


from tortoolkit.serverv2.setup import app
from tortoolkit.search_server.main import app as searchapp
from .database.dbhandler import TorToolkitDB,TtkTorrents, UserDB, TtkUpload
from .core.varholdern import VarHolder
import time
logging.info("Database created")
upload_db = TtkUpload()
var_db = TorToolkitDB()
tor_db = TtkTorrents()
user_db = UserDB()
transfer = [0,0] # UP,DOWN

uptime = time.time()
to_del = []
SessionVars = VarHolder(var_db)