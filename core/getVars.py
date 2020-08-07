from tortoolkit.consts.ExecVarsSample import ExecVars 
import os

def get_val(variable):
    val = None

    #Get the variable from the constants supplied
    try:
        val = getattr(ExecVars,variable)
    except AttributeError:pass

    #Get the variable form the env [overlap]
    #try:
    envval = os.environ.get(variable)
    val =  envval if envval is not None else val

    #Get the variable form the DB [overlap]
    #TODO database

    if val is None:
        raise Exception("The variable was not found in either the constants, environment or database. Variable is :- {}".format(variable))
    
    if isinstance(val,str):
        val = val.strip()

    return val