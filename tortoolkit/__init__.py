#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = "0.1.3"
__author__ = "YashDK Github@yash-dk"

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(),logging.FileHandler("torlog.txt")]
)

from tortoolkit.core.server import start_server
from .core.database_handle import TtkUpload,TorToolkitDB,TtkTorrents, UserDB
from .core.varholder import VarHolder

logging.info("Database created")
upload_db = TtkUpload()
var_db = TorToolkitDB()
tor_db = TtkTorrents()
user_db = UserDB()

SessionVars = VarHolder(var_db)