from tortoolkit.consts.DefaultCommands import Commands
import os

def get_command(command):
    cmd = None

    #Get the command from the constants supplied
    try:
        cmd = getattr(Commands,command)
    except AttributeError:pass

    #Get the commands form the env [overlap]
    #try:
    envcmd = os.environ.get(command)
    cmd =  envcmd if envcmd is not None else cmd

    #Get the commands form the DB [overlap]
    #TODO database

    if cmd is None:
        raise Exception("The command was not found in either the constants, environment or database. Command is :- {}".format(command))
    
    cmd = cmd.strip("/")

    return f"/{cmd}"