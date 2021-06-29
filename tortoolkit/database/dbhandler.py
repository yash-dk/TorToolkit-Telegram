from ..consts.ExecVarsSample import ExecVars
import os

dburl = os.environ.get("DB_URI",None)
if dburl is None:
    dburl = ExecVars.DB_URI

if "mongo" in dburl:
    from .mongo_impl import TorToolkitDB, UserDB, TtkTorrents
else:
    from .postgres_impl import TorToolkitDB, UserDB, TtkTorrents
