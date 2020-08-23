__version__ = "0.0.2"
__author__ = "YashDK Github@yash-dk"

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s"
)
from tortoolkit.core.server import start_server
from .core.database_handle import TtkUpload,TorToolkitDB
logging.info("Database created")
upload_db = TtkUpload()
var_db = TorToolkitDB()