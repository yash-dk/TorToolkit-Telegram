# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from .base_status import BaseStatus
from ..utils.human_format import human_readable_bytes, human_readable_timedelta
from telethon.tl.types import KeyboardButtonCallback

class QbittorrentStatus(BaseStatus):
    def __init__(self, controller, downloader=None, sender_id=None):
        self._controller = controller
        self._downloader = downloader
        self._sender_id = sender_id

    async def update_now(self):
        if self._downloader is None:
            self._downloader = await self._controller.get_downloader()

        self._update_message = await self._controller.get_update_message()

        self._torrent = await self._downloader.get_update()

        # Construct the status message
        data = "torcancel {} {}".format(self._downloader.get_hash(), self._sender_id)
        if self._torrent is not None:
            await self._update_message.edit(await self.create_message(), parse_mode="html", buttons=[KeyboardButtonCallback("Cancel Leech",data=data.encode("UTF-8"))])

    async def create_message(self):
        msg = "<b>Downloading:</b> <code>{}</code>\n".format(
            self._torrent.name
            )
        msg += "<b>Down:</b> {} <b>Up:</b> {}\n".format(
            human_readable_bytes(self._torrent.dlspeed,postfix="/s"),
            human_readable_bytes(self._torrent.upspeed,postfix="/s")
            )
        msg += "<b>Progress:</b> {} - {}%\n".format(
            self.progress_bar(self._torrent.progress),
            round(self._torrent.progress*100,2)
            )
        msg += "<b>Downloaded:</b> {} of {}\n".format(
            human_readable_bytes(self._torrent.downloaded),
            human_readable_bytes(self._torrent.total_size)
            )
        msg += "<b>ETA:</b> <b>{}</b>\n".format(
            human_readable_timedelta(self._torrent.eta)
            )
        msg += "<b>S:</b>{} <b>L:</b>{}\n".format(
            self._torrent.num_seeds,self._torrent.num_leechs
            )
        msg += "<b>Using engine:</b> <code>qBittorrent</code>"

        return msg

    def get_type(self):
        return self.QBIT
    
    def get_sender_id(self):
        return self._sender_id