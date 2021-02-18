#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = "0.1.6"
__author__ = "YashDK Github@yash-dk"

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(),logging.FileHandler("torlog.txt")]
)

from tortoolkit.core.wserver import start_server
from .core.database_handle import TtkUpload,TorToolkitDB,TtkTorrents, UserDB
from .core.varholdern import VarHolder
import time

logging.info("Database created")
upload_db = TtkUpload()
var_db = TorToolkitDB()
tor_db = TtkTorrents()
user_db = UserDB()

uptime = time.time()

SessionVars = VarHolder(var_db)