# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta

class TGUploadStatus(BaseStatus):
    def __init__(self, downloader, sender_id=None):
        self._downloader = downloader
        self._sender_id = sender_id

    async def update_now(self):

        self._up_task = await self._downloader.get_update()
        return

    async def create_message(self):
        msg = f"<b>Uploading:</b> <code>{self._up_task.current_file}</code>\n"
        try:
            percent = self._up_task.current_done/ self._up_task.current_total
        except:
            percent = 0
        msg += self.progress_bar(percent)
        msg += " - {}%\n{} of {}\nSpeed: {}/s\nETA: {}\nUsing engine: Telethon".format(round(percent), human_readable_bytes(self._up_task.current_done), 
        human_readable_bytes(self._up_task.current_total), human_readable_bytes(self._up_task.current_speed), self._up_task.current_eta)

        return msg

    def get_type(self):
        return self.TGUP
    
    def get_sender_id(self):
        return self._sender_id