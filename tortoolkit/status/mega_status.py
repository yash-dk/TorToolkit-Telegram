# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta
from telethon.tl.types import KeyboardButtonCallback

class MegaStatus(BaseStatus):
    def __init__(self, controller, downloader=None, sender_id=None):
        self._controller = controller
        self._downloader = downloader
        self._sender_id = sender_id

    async def update_now(self):
        if self._downloader is None:
            self._downloader = await self._controller.get_downloader()

        self._update_message = await self._controller.get_update_message()

        self._dl_task = await self._downloader.get_update()

        # Construct the status message
        data = "torcancel megadl {} {}".format(
                self._downloader.get_gid(),
                self._sender_id
            )
        if self._dl_task is not None:
            await self._update_message.edit(await self.create_message(), parse_mode="html", buttons=[KeyboardButtonCallback("Cancel Mega Leech",data=data.encode("UTF-8"))])

    async def create_message(self):

        msg = "<b>Downloading:</b> <code>{}</code>\n".format(
            self._dl_task["name"]
            )
        msg += "<b>Speed:</b> {}\n".format(
            human_readable_bytes(self._dl_task["speed"])
            )
        msg += "<b>Progress:</b> {} - {}%\n".format(
            self.progress_bar((self._dl_task["completed_length"]/self._dl_task["total_length"])),
            round((self._dl_task["completed_length"]/self._dl_task["total_length"])*100, 2)
            )
        msg += "<b>Downloaded:</b> {} of {}\n".format(
            human_readable_bytes(self._dl_task["completed_length"]),
            human_readable_bytes(self._dl_task["total_length"])
            )
        msg += "<b>ETA:</b> <b>N/A</b>\n"
        
        msg += "<b>Using engine:</b> <code>Mega DL</code>"

        return msg

    def get_type(self):
        return self.MEGA
    
    def get_sender_id(self):
        return self._sender_id