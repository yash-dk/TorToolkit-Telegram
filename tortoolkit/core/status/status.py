# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
import logging
from ...functions.Human_Format import human_readable_bytes, human_readable_timedelta
from ..getVars import get_val
from telethon.errors.rpcerrorlist import MessageNotModifiedError, FloodWaitError
from datetime import datetime

torlog = logging.getLogger(__name__)

class Status():
    # Shared List
    Tasks = []
    
    def __init__(self):
        self._task_id = len(self.Tasks) + 1

    def refresh_info(self):
        raise NotImplementedError

    def update_message(self):
        raise NotImplementedError

# qBittorrent Task Class
class QBTask(Status):
    
    def __init__(self, torrent, message, client):
        super().__init__()
        self.hash = torrent.hash
        self._torrent = torrent
        self._message = message
        self._client = client
        self._active = True
        self._path = torrent.save_path
        self._error = ""
        self._done = False
        self.cancel = False
        self._omess = None
    
    async def set_original_mess(self, omess):
        self._omess = omess

    async def refresh_info(self, torrent = None):
        if torrent is None:
            self._torrent = self._client.torrents_info(torrent_hashes=self._torrent.hash)
        else:
            self._torrent = torrent

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
        msg += "<b>ETA:</b> <b>{} Mins</b>\n".format(
            human_readable_timedelta(self._torrent.eta)
            )
        msg += "<b>S:</b>{} <b>L:</b>{}\n".format(
            self._torrent.num_seeds,self._torrent.num_leechs
            )
        msg += "<b>Using engine:</b> <code>qBittorrent</code>"

        return msg

    async def get_state(self):
        #stalled
        if self._torrent.state == "stalledDL":
            return"Torrent <code>{}</code> is stalled(waiting for connection) temporarily.".format(self._torrent.name)
        #meta stage
        elif self._torrent.state == "metaDL":
            return  "Getting metadata for {} - {}".format(self._torrent.name,datetime.now().strftime("%H:%M:%S"))
        elif self._torrent.state == "downloading" or self._torrent.state.lower().endswith("dl"):
            # kept for past ref
            return None

    async def central_message(self):
        cstate = await self.get_state()
        if cstate is not None:
            return cstate
        else:
            return await self.create_message()

    async def update_message(self):
        msg = await self.create_message()
        try:
        
            cstate = await self.get_state()
            
            msg = cstate if cstate is not None else msg
            
            await self._message.edit(msg,parse_mode="html",buttons=self._message.reply_markup) 

        except (MessageNotModifiedError,FloodWaitError) as e:
            torlog.error("{}".format(e))

    async def set_done(self):
        self._done = True
        await self.set_inactive()

    def is_done(self):
        return self._done

    async def set_inactive(self, error=None):
        self._active = False
        if error is not None:
            self._error = error

    def progress_bar(self, percentage):
        """Returns a progress bar for download
        """
        #percentage is on the scale of 0-1
        comp = get_val("COMPLETED_STR")
        ncomp = get_val("REMAINING_STR")
        pr = ""

        for i in range(1,11):
            if i <= int(percentage*10):
                pr += comp
            else:
                pr += ncomp
        return pr