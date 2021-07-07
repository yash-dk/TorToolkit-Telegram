#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from telethon import TelegramClient
#from tortoolkit.core.HandleManager import add_handlers
#from tortoolkit.core.getVars import get_val
#import logging,asyncio
#from tortoolkit.core.wserver import start_server_async
#from tortoolkit.core.status.auto_delete import del_status
#from pyrogram import Client
#try:
#    from tortoolkit.functions.rstuff import get_rstuff
#except ImportError:pass
#
#from tortoolkit.ttk_client import TortkClient
#
#if __name__ == "__main__":
#
#    #logging stuff
#    #thread name is just kept for future use
#    logging.basicConfig(
#        level=logging.INFO,
#        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s"
#    )
#    logging.getLogger("pyrogram").setLevel(logging.ERROR)
#    
#    # parallel connections limiter
#    queue = asyncio.Queue()
#    exqueue = asyncio.Queue()
#    
#    for i in range(1,4):
#        queue.put_nowait(i)
#
#    for i in range(1,5):
#        exqueue.put_nowait(i)
#    
#    # Telethon client creation
#    ttkbot = TortkClient("TorToolkitBot",get_val("API_ID"),get_val("API_HASH"), #timeout=20, retry_delay=3, request_retries=10, connection_retries=10)
#    ttkbot.queue = queue
#    ttkbot.exqueue = exqueue
#    ttkbot.start(bot_token=get_val("BOT_TOKEN"))
#    logging.info("Telethon Client created.")
#
#    # Pyro Client creation and linking
#    pyroclient = Client("pyrosession", api_id=get_val("API_ID"), api_hash=get_val#("API_HASH"), bot_token=get_val("BOT_TOKEN"), workers=100)
#    pyroclient.start()
#    ttkbot.pyro = pyroclient
#    logging.info("Pryogram Client created.")
#
#    # Associate the handlers
#    add_handlers(ttkbot)
#
#    ttkbot.loop.create_task(del_status())
#
#    if get_val("IS_VPS"):
#        ttkbot.loop.run_until_complete(start_server_async(get_val("SERVPORT")))
#    try:
#        ttkbot.loop.run_until_complete(get_rstuff())
#    except:pass
#    
#    logging.info("THE BOT IS READY TO GOOOOOOO")
#
#    ttkbot.run_until_disconnected()

from .downloaders.qbittorrent_downloader import QbittorrentDownloader
import asyncio

async def main():
    mag = "magnet:?xt=urn:btih:8E59D91F7C89D5CFA691D5BE4C2A5A6B466C40B0&dn=The.Colony.2021.720p.WEBRip.800MB.x264-GalaxyRG&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ffasttracker.foreverpirates.co%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Fexplodie.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Fipv4.tracker.harry.lu%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.uw0.xyz%3A6969%2Fannounce&tr=udp%3A%2F%2Fopentracker.i2p.rocks%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.birkenwald.de%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Ftracker.moeking.me%3A6969%2Fannounce&tr=udp%3A%2F%2Fopentor.org%3A2710%2Fannounce&tr=udp%3A%2F%2Ftracker.dler.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.zer0day.to%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969%2Fannounce&tr=udp%3A%2F%2Fcoppersurfer.tk%3A6969%2Fannounce"

    bitdown = QbittorrentDownloader(mag,123)
    await bitdown.register_torrent()
    res = await bitdown.update_progress()
    print(res)

if __name__ == "__main__":
    loop= asyncio.get_event_loop()
    loop.run_until_complete(main())