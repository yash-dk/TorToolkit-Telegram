from telethon import TelegramClient
from tortoolkit.core.HandleManager import add_handlers
from tortoolkit.core.getVars import get_val
import logging

if __name__ == "__main__":

    #logging stuff
    #thread name is just kept for future use
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s"
    )
    
    ttkbot = TelegramClient("TorToolkitBot",get_val("API_ID"),get_val("API_HASH"))
    ttkbot.start(bot_token=get_val("BOT_TOKEN"))

    add_handlers(ttkbot)

    ttkbot.run_until_disconnected()