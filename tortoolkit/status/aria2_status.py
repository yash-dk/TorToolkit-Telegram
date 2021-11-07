# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta
from telethon.tl.types import KeyboardButtonCallback

class Aria2Status(BaseStatus):
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
        data = "torcancel aria2 {} {}".format(
                self._downloader.get_gid(),
                self._sender_id
            )
        msg = "Aria2 Task Running."
        if self._dl_task is not None:
            msg = await self.create_message()
            if not get_msg:
                await self._update_message.edit(msg, parse_mode="html", buttons=[KeyboardButtonCallback("Cancel Direct Leech",data=data.encode("UTF-8"))])
        
        if get_msg:
            return msg, data
    async def create_message(self):
        downloading_dir_name = "N/A"
        try:
            downloading_dir_name = str(self._dl_task.name)
        except:
            pass

        msg = "<b>Downloading:</b> <code>{}</code>\n".format(
            downloading_dir_name
            )
        msg += "<b>Down:</b> {} <b>Up:</b> {}\n".format(
            self._dl_task.download_speed_string(),
            self._dl_task.upload_speed_string()
            )
        msg += "<b>Progress:</b> {} - {}%\n".format(
            self.progress_bar(self._dl_task.progress/100),
            round(self._dl_task.progress,2)
            )
        msg += "<b>Downloaded:</b> {} of {}\n".format(
            human_readable_bytes(self._dl_task.completed_length),
            human_readable_bytes(self._dl_task.total_length)
            )
        msg += "<b>ETA:</b> <b>{}</b>\n".format(
            self._dl_task.eta_string()
            )
        msg += "<b>Conns:</b>{} <b>\n".format(
            self._dl_task.connections
            )
        msg += "<b>Using engine:</b> <code>Aria2 For DirectLinks</code>"

        return msg

    def get_type(self):
        return self.ARIA2
    
    def get_sender_id(self):
        return self._sender_id