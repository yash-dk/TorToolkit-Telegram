import re
from typing import AbstractSet
from pymongo import MongoClient
from .abstract_db import AbstractDatabase

class MongoDB(AbstractDatabase):
    # No Impl for Intermediate class as no clean up required
    def __init__(self, dburl) -> None:
        self._client = MongoClient(dburl)
    
        self._db = self._client.TTKDB

    def get_client(self):
        return self._client
    
    def get_db(self):
        return self._db