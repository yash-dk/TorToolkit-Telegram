# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import psycopg2, logging

torlog = logging.getLogger(__name__)

class DataBaseHandle:
    _active_connections = []
    _connection_users = []
    def __init__(self,dburl=None):
        """Load the DB URL if available
        """
        self._dburl = dburl
        if isinstance(self._dburl,bool):
            self._block = True
        else:
            self._block = False
        
        if self._block:
            return
        
        if self._active_connections:
            self._conn = self._active_connections[0]
            self._connection_users.append(1)
        else:
            torlog.debug("Established Connection")
            self._conn = psycopg2.connect(self._dburl)
            self._connection_users.append(1)
            self._active_connections.append(self._conn)

    def scur(self):
        # start cursor
        cur = self._conn.cursor()
        return cur

    def ccur(self,cursor):
        if cursor is not None:
            self._conn.commit()
            cursor.close()


    def __del__(self):
        """Close connection so that the threshold is not exceeded
        """
        if self._block:
            return
        self._connection_users.pop()
        
        if not self._connection_users:
            self._conn.close()