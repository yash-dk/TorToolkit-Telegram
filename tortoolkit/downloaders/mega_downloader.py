# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from ..core.base_task import BaseTask
import logging
from ..core.getVars import get_val
from subprocess import Popen
from megasdkrestclient import MegaSdkRestClient, errors, constants
from ..status.mega_status import MegaStatus
from ..status.status_manager import StatusManager
import asyncio
import time
import pathlib
import os
from functools import partial

torlog = logging.getLogger(__name__)

class MegaDownloader(BaseTask):
    CLI_LIST = []
    def __init__(self, link, from_user_id):
        super().__init__()
        self._client = None 
        self._process = None
        self._link = link
        self._from_user_id = from_user_id
        self._update_info = None
        self._gid = 0
        self._aloop = asyncio.get_event_loop()

    
    async def init_mega_client(self, return_pr=False):
        if len(self.CLI_LIST) > 0:
            if return_pr:
                return self.CLI_LIST[1]
            else:
                return self.CLI_LIST[0]
        
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
            self.CLI_LIST.append(mega_client)
            self.CLI_LIST.append(pr)
        
        if return_pr:
            return self._process
        else:
            return self._client

    async def execute(self):
        mega_client = await self.init_mega_client()

        path = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".",""))
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        
        try:
            dl_add_info = await self._aloop.run_in_executor(None, partial(mega_client.addDl,self._link, path))
        except errors.MegaSdkRestClientException as e:
            self._error_reason = str(dict(e.message)["message"]).title()
            self._is_errored = True
            return
        
        self._gid  = dl_add_info["gid"]
        
        dl_info = await self._aloop.run_in_executor(None, partial(mega_client.getDownloadInfo,dl_add_info["gid"]))
        
        self._path = os.path.join(dl_add_info["dir"], dl_info["name"])
        
        self._update_info = dl_info

        while True:
            dl_info = await self._aloop.run_in_executor(None, partial(mega_client.getDownloadInfo, dl_add_info["gid"]))
            if (dl_info["total_length"]/(1024*1024*1024)) > get_val("MAX_MEGA_LIMIT"):
                await self.remove_mega_dl(self._gid) 
                self._is_errored = True
                self._error_reason = "The mega link is oversized."
                return
            
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
    
    async def remove_mega_dl(self, gid):
        mega_client = await self.init_mega_client()
        await self._aloop.run_in_executor(None, partial(mega_client.cancelDl,gid))

    def get_gid(self):
        return self._gid

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
    all_tasks = []
    def __init__(self, dl_link, user_msg, new_name=None):
        self._dl_link = dl_link
        self._user_msg = user_msg
        self._new_name = new_name

    async def execute(self):
        self._update_msg = await self._user_msg.reply("Starting the Mega DL Download.")

        self._mega_down = MegaDownloader(self._dl_link, self._user_msg.sender_id)

        self.all_tasks.append(self)
        # Status update active
        status_mgr = MegaStatus(self,self._mega_down,self._user_msg.sender_id)
        StatusManager().add_status(status_mgr)
        status_mgr.set_active()

        res = await self._mega_down.execute()

        # Status update inactive
        status_mgr.set_inactive()
        self.all_tasks.remove(self)

        if self._mega_down.is_errored or self._mega_down.is_canceled:
            await self._update_msg.edit("Your Task was unsccuessful. {}".format(self._mega_down.get_error_reason()), buttons=None)
            return False
        else:
            if self._mega_down.is_completed:
                await self._update_msg.edit(self._mega_down.get_error_reason(), buttons=None)
            
            return res
    
    async def get_update_message(self):
        return self._update_msg

    async def get_downloader(self):
        return self._mega_down