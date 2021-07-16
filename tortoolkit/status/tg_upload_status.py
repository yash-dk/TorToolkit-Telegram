# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta

class TGUploadStatus(BaseStatus):
    def __init__(self, downloader, sender_id=None):
        self._downloader = downloader
        self._sender_id = sender_id

    async def update_now(self, get_msg = False):

        self._up_task = await self._downloader.get_update()
        msg = "Telegram UP Task Running."
        up_msg = await self._downloader.get_update_message()
        data = "..."
        if up_msg is not None:
            data = "upcancel {} {} {}".format(up_msg.chat_id,up_msg.id,self._sender_id)
        
        if self._up_task is not None:
            msg = await self.create_message()
        
        if get_msg:
            return msg, data
        return

    async def create_message(self):
        try:
            percent = self._up_task.current_done/ self._up_task.current_total
        except:
            percent = 0
        try:
            perc = self._up_task.uploaded_files / self._up_task.files
        except:
            perc = 0
        
        msg = f"<b>Overall TG UP progress:-<b>\n"
        msg += self.progress_bar(perc) + f" - {round(perc*100, 2)}\n"
        msg += f"<b>Uploading:</b> <code>{self._up_task.current_file}</code>\n"
        
        msg += self.progress_bar(percent)
        msg += " - {}%\n{} of {}\nSpeed: {}/s\nETA: {}\nUsing engine: Telethon".format(round(percent*100, 2), human_readable_bytes(self._up_task.current_done), 
        human_readable_bytes(self._up_task.current_total), human_readable_bytes(self._up_task.current_speed), self._up_task.current_eta)

        return msg

    def get_type(self):
        return self.TGUP
    
    def get_sender_id(self):
        return self._sender_id