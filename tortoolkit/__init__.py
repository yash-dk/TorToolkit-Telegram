#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = "0.2.6-heroku-master"
__author__ = "AmirulAndalib [amirulandalib@github]"

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("torlog.txt")],
)

import time

from tortoolkit.core.wserver import start_server

from .core.database_handle import TorToolkitDB, TtkTorrents, TtkUpload, UserDB
from .core.varholdern import VarHolder

logging.info("Database created")
upload_db = TtkUpload()
var_db = TorToolkitDB()
tor_db = TtkTorrents()
user_db = UserDB()
transfer = [0, 0]  # UP,DOWN

uptime = time.time()
to_del = []
SessionVars = VarHolder(var_db)
