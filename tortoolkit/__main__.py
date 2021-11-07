#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telethon import TelegramClient
from tortoolkit.core.HandleManager import add_handlers
from tortoolkit.core.getVars import get_val
import logging,asyncio
from tortoolkit.server.server import start_server_async
from pyrogram import Client
from .status.status_manager import StatusManager
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
    logging.getLogger("pyrogram").setLevel(logging.ERROR)
    
    # parallel connections limiter
    queue = asyncio.Queue()
    exqueue = asyncio.Queue()
    
    for i in range(1,4):
        queue.put_nowait(i)

    for i in range(1,5):
        exqueue.put_nowait(i)
    
    # Telethon client creation
    ttkbot = TortkClient("TorToolkitBot",get_val("API_ID"),get_val("API_HASH"), timeout=20, retry_delay=3, request_retries=10, connection_retries=10)
    ttkbot.queue = queue
    ttkbot.exqueue = exqueue
    ttkbot.start(bot_token=get_val("BOT_TOKEN"))
    logging.info("Telethon Client created.")

    # Pyro Client creation and linking
    pyroclient = Client("pyrosession", api_id=get_val("API_ID"), api_hash=get_val("API_HASH"), bot_token=get_val("BOT_TOKEN"), workers=100)
    pyroclient.start()
    ttkbot.pyro = pyroclient
    logging.info("Pryogram Client created.")

    # Associate the handlers
    add_handlers(ttkbot)

    status_mgr = StatusManager()

    ttkbot.loop.create_task(status_mgr.status_poller())

    if get_val("IS_VPS"):
        ttkbot.loop.run_until_complete(start_server_async(get_val("SERVPORT")))
    try:
        ttkbot.loop.run_until_complete(get_rstuff())
    except:pass
    
    logging.info("THE BOT IS READY TO GOOOOOOO")

    ttkbot.run_until_disconnected()

#import asyncio
#from .downloaders.direct_link_gen import DLGen
#
#async def main():
#    ...
#
#if __name__ == "__main__":
#    loop = asyncio.get_event_loop()
#    loop.run_until_complete(main())