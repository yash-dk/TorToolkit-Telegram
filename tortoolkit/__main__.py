#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telethon import TelegramClient
from tortoolkit.core.HandleManager import add_handlers
from tortoolkit.core.getVars import get_val
import logging,asyncio
from tortoolkit.core.server import start_server_async
try:
    from tortoolkit.functions.rstuff import get_rstuff
except ImportError:pass

from tortoolkit.ttk_client import TortkClient

if __name__ == "__main__":

    #logging stuff
    #thread name is just kept for future use
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s"
    )
    
    # parallel connections limiter
    queue = asyncio.Queue()
    for i in range(1,4):
        queue.put_nowait(i)

    ttkbot = TortkClient("TorToolkitBot",get_val("API_ID"),get_val("API_HASH"))
    ttkbot.queue = queue
    ttkbot.start(bot_token=get_val("BOT_TOKEN"))
    
    add_handlers(ttkbot)

    if get_val("IS_VPS"):
        ttkbot.loop.run_until_complete(start_server_async())
    try:
        ttkbot.loop.run_until_complete(get_rstuff())
    except:pass
    
    ttkbot.run_until_disconnected()