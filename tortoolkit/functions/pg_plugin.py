# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import psycopg2

class DataBaseHandle:
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
        
        self._conn = psycopg2.connect(self._dburl)

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
        self._conn.close()