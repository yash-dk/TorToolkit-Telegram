# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta
from telethon.tl.types import KeyboardButtonCallback

class RcloneStatus(BaseStatus):
    def __init__(self, controller, downloader=None, sender_id = None):
        self._controller = controller
        self._downloader = downloader
        self._sender_id = sender_id

    async def update_now(self, get_msg = False):
        if self._downloader is None:
            self._downloader = await self._controller.get_downloader()

        self._update_message = await self._controller.get_update_message()

        self._up_task = await self._downloader.get_update()

        # Construct the status message
        user_msg = await self._controller.get_user_message()
        data = "upcancel {} {} {}".format(user_msg.chat_id,user_msg.id,user_msg.sender_id)
        
        msg = "Rclone Task Running."
        if self._up_task is not None:
            msg = await self.create_message()
            if not get_msg:
                await self._update_message.edit(await self.create_message(), parse_mode="html", buttons = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))])

        if get_msg:
            return msg, data

    async def create_message(self):
        try:
            prg = int(self._up_task.prg)
        except:
            prg = 0
        prg = "{} - {}%".format(self.progress_bar(prg/100), prg)
        msg = "<b>Uploaded:- {} \n{} \nSpeed:- {} \nETA:- {}</b> \n<b>Using Engine:- </b><code>RCLONE</code>".format(self._up_task.uploaded,prg,self._up_task.speed,self._up_task.eta.replace("ETA",""))

        return msg

    def get_type(self):
        return self.RCLUP
    
    def get_sender_id(self):
        return self._sender_id