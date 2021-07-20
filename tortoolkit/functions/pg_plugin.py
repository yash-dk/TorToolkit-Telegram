# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import logging
import time

import psycopg2

torlog = logging.getLogger(__name__)


class DataBaseHandle:
    _active_connections = []
    _connection_users = []

    def __init__(self, dburl=None):
        """Load the DB URL if available"""
        self._dburl = dburl
        if isinstance(self._dburl, bool):
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

    def scur(self, dictcur=False):
        # start cursor
        cur = None
        for i in range(0, 5):
            try:
                if dictcur:
                    cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                else:
                    cur = self._conn.cursor()

                break
            except psycopg2.InterfaceError:
                torlog.info(
                    f"Attempting to Re-establish the connection to server {i} times."
                )
                self.re_establish()

        return cur

    def re_establish(self):
        try:
            if self._active_connections[0].closed != 0:
                torlog.info("Re-establish Success.")
                self._conn = psycopg2.connect(self._dburl)
                self._active_connections[0] = self._conn
            else:
                torlog.info("Re-establish Success Cache.")
                self._conn = self._active_connections[0]
        except:
            time.sleep(1)  # Blocking call ... this stage is panic.

    def ccur(self, cursor):
        if cursor is not None:
            self._conn.commit()
            cursor.close()

    def __del__(self):
        """Close connection so that the threshold is not exceeded"""
        if self._block:
            return
        self._connection_users.pop()

        if not self._connection_users:
            self._conn.close()
