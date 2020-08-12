import psycopg2
from ..functions.pg_plugin import DataBaseHandle

#this will handel the transaction with completed torrents
class TorToolkitDB(DataBaseHandle):
    def __init__(self,dburl):
        super().__init__(dburl)

    

    def __del__(self):
        super().__del__()