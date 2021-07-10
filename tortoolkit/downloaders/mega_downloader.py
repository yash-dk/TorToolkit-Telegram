from ..core.base_task import BaseTask
import logging
from ..core.getVars import get_val
from subprocess import Popen
from megasdkrestclient import MegaSdkRestClient, errors, constants
import asyncio
import time
import pathlib
import os

torlog = logging.getLogger(__name__)

class MegaDownloader(BaseTask):
    def __init__(self, link, from_user_id):
        super().__init__()
        self._client = None 
        self._process = None
        self._link = link
        self._from_user_id = from_user_id

    
    async def init_mega_client(self, return_pr=False):
        # TODO add var for the port for the mega client.
        if self._client is None and self._process is None:
            MEGA_API = get_val("MEGA_API")
            MEGA_UNAME = get_val("MEGA_UNAME")
            MEGA_PASS = get_val("MEGA_PASS")
            
            if MEGA_API is None:
                return None
            
            pr = Popen(["megasdkrest", "--apikey", MEGA_API,"--port", "8200"])
            await asyncio.sleep(5)
            mega_client = MegaSdkRestClient("http://localhost:8200")
            
            anon = False
            if MEGA_UNAME is None:
                anon = True
                torlog.warn("Mega Username not specified")
            
            if MEGA_PASS is None:
                anon = True
                torlog.warn("Mega Password not specified")
            
            if anon:
                torlog.info("Mega running in Anon mode.")
                
            else:
                torlog.info("Mega running in Logged in mode.")
                
                try:
                    mega_client.login(MEGA_UNAME, MEGA_PASS)
                except:
                    torlog.error("Mega login failed.")
                    torlog.info("Started in anon mode.")

            self._client = mega_client 
            self._process = pr
        
        if return_pr:
            return self._process
        else:
            return self._client

    async def execute(self):
        mega_client = await self.init_mega_client()

        path = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".",""))
        pathlib.Path(path).mkdir(parents=True, exist_ok=True) 
        dl_add_info = mega_client.addDl(self._link, path)
        self._gid  = dl_add_info["gid"]
        self._path = dl_add_info["dir"]
        
        dl_info = mega_client.getDownloadInfo(dl_add_info["gid"])
        
        self._update_info = dl_info

        while True:
            dl_info = mega_client.getDownloadInfo(dl_add_info["gid"])
            if dl_info["state"] not in [constants.State.TYPE_STATE_CANCELED,constants.State.TYPE_STATE_FAILED]:
                if dl_info["state"] == constants.State.TYPE_STATE_COMPLETED:
                    self._is_completed = True
                    self._error_reason = "Download Complete."
                    await asyncio.sleep(2)
                    return self._path
                try:
                    self._update_info = dl_info
                    await asyncio.sleep(get_val("EDIT_SLEEP_SECS"))
                except Exception as e:
                    torlog.info(e)
            else:
                if dl_info["state"] == constants.State.TYPE_STATE_CANCELED:
                    self._is_canceled = True
                    self._error_reason = "Canceled by user."
                else:
                    self._is_errored = True
                    self._error_reason = dl_info["error_string"]
                return False
    def cancel(self, is_admin=False):
        self._is_canceled = True
        if is_admin:
            self._canceled_by = self.ADMIN
        else: 
            self._canceled_by = self.USER
    
    async def get_update(self):
        return self._update_info

    def get_error_reason(self):
        return self._error_reason
    
class MegaController:
    def __init__(self, dl_link, user_msg, new_name=None):
        self._dl_link = dl_link
        self._user_msg = user_msg
        self._new_name = new_name

    async def execute(self):
        self._update_msg = await self._user_msg.reply("Starting the Mega DL Download.")

        self._mega_down = MegaDownloader(self._dl_link, self._user_msg.sender_id)

        res = await self._mega_down.execute()

        if self._mega_down.is_errored:
            await self._update_msg.edit("Your Task was unsccuessful. {}".format(self._mega_down.get_error_reason()))
            return False
        else:
            if self._mega_down.is_completed:
                await self._update_msg.edit(self._mega_down.get_error_reason())    
            
            return res
    
    async def get_update_message(self):
        return self._update_msg

    async def get_downloader(self):
        return self._mega_down