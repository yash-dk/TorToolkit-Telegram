# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import logging
import os

from ..consts.DefaultCommands import Commands
from ..core.getVars import get_val

torlog = logging.getLogger(__name__)


def get_command(command):
    cmd = None

    # Get the command from the constants supplied
    try:
        cmd = getattr(Commands, command)
        torlog.debug(f"Getting the command {command} from file:- {cmd}")
    except AttributeError:
        pass

    # Get the commands form the env [overlap]
    # try:
    envcmd = os.environ.get(command)
    torlog.debug(f"Getting the command {command} from file:- {envcmd}")
    cmd = envcmd if envcmd is not None else cmd

    # Get the commands form the DB [overlap]
    # TODO database

    if cmd is None:
        torlog.debug(f"None Command Error occured for command {command}")
        raise Exception(
            "The command was not found in either the constants, environment or database. Command is :- {}".format(
                command
            )
        )

    cmd = cmd.strip("/")
    cmd += get_val("BOT_CMD_POSTFIX")

    torlog.debug(f"Final resolver for {command} is {cmd}")
    return f"/{cmd}"
