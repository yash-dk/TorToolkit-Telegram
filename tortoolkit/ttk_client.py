from telethon import TelegramClient
import asyncio

class TortkClient(TelegramClient):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        
        #for now only queue is required
        self.queue = None