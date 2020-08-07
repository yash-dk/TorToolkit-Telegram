from telethon import TelegramClient
from tortoolkit.core.HandleManager import add_handlers
from tortoolkit.core.getVars import get_val

if __name__ == "__main__":

    ttkbot = TelegramClient("TorToolkitBot",get_val("API_ID"),get_val("API_HASH"))
    ttkbot.start(bot_token=get_val("BOT_TOKEN"))

    add_handlers(ttkbot)    

    ttkbot.run_until_disconnected()