# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta
from telethon.tl.types import KeyboardButtonCallback

class YTDLStatus(BaseStatus):
    def __init__(self, controller, downloader=None, sender_id=None):
        self._controller = controller
        self._downloader = downloader
        self._sender_id = sender_id

    async def update_now(self, get_msg = False):
        if self._downloader is None:
            self._downloader = await self._controller.get_downloader()

        self._update_message = await self._controller.get_update_message()

        self._dl_task = await self._downloader.get_update()

        # Construct the status message
        # Add cancel login here
        msg = "YTDL/PYTDL Task Running."
        user_msg = await self._controller.get_user_message()
        data = "upcancel {} {} {}".format(user_msg.chat_id,user_msg.id,user_msg.sender_id)

        if self._dl_task is not None:
            msg = await self.create_message()
            if not get_msg:
                await self._update_message.edit(await self.create_message(), parse_mode="html", buttons=[KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))])
            
        if get_msg:
            return msg, data

    async def create_message(self):
        

        msg = "<b>Downloading:</b> <code>{}</code>\n".format(
            self._dl_task["filename"]
            )
        msg += "<b>Down:</b> {}\n".format(
            self._dl_task["_speed_str"]
            )
        try:
            perce = self._dl_task["_percent_str"].strip("%")
            perce = float(perce)
        except:
            perce = 0
        
        msg += "<b>Progress:</b> {} - {}\n".format(
            self.progress_bar(perce/100),
            self._dl_task["_percent_str"]
            )
        msg += "<b>Downloaded:</b> {} of {}\n".format(
            human_readable_bytes(self._dl_task["downloaded_bytes"]),
            human_readable_bytes(self._dl_task["total_bytes"])
            )
        msg += "<b>ETA:</b> <b>{} Mins</b>\n".format(
            human_readable_timedelta(self._dl_task["eta"])
            )
        msg += "<b>Using engine:</b> <code>YTDL</code>"

        return msg

    def get_type(self):
        return self.YTDL
    
    def get_sender_id(self):
        return self._sender_id