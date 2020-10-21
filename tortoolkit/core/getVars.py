from ..consts.ExecVarsSample import ExecVars
#from ..core.database_handle import TorToolkitDB
from tortoolkit import SessionVars
import os

def get_val(variable):
    return SessionVars.get_var(variable)

