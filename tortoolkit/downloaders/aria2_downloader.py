from ..status.status_manager import StatusManager
from ..core.base_task import BaseTask
import logging
import asyncio
from functools import partial
import aria2p
import os
import time
from ..core.getVars import get_val
from telethon.errors.rpcerrorlist import MessageNotModifiedError
from ..status.aria2_status import Aria2Status

torlog = logging.getLogger(__name__)

class Aria2Downloader(BaseTask):
    def __init__(self, dl_link, from_user_id, new_file_name=None):
        super().__init__()
        self._aloop = asyncio.get_event_loop()
        self._client = None
        self._dl_link = dl_link
        self._from_user_id = from_user_id
        self._new_file_name = new_file_name 
        self._aloop = asyncio.get_event_loop()
        self._gid = 0

    async def get_client(self):
        
        if self._client is not None:
            return self._client

        # TODO add config vars for port
        aria2_daemon_start_cmd = []
        
        aria2_daemon_start_cmd.append("aria2c")
        aria2_daemon_start_cmd.append("--daemon=true")
        aria2_daemon_start_cmd.append("--enable-rpc")
        aria2_daemon_start_cmd.append("--disk-cache=0")
        aria2_daemon_start_cmd.append("--follow-torrent=false")
        aria2_daemon_start_cmd.append("--max-connection-per-server=10")
        aria2_daemon_start_cmd.append("--min-split-size=10M")
        aria2_daemon_start_cmd.append("--rpc-listen-all=true")
        aria2_daemon_start_cmd.append(f"--rpc-listen-port=8100")
        aria2_daemon_start_cmd.append("--rpc-max-request-size=1024M")
        aria2_daemon_start_cmd.append("--seed-ratio=0.0")
        aria2_daemon_start_cmd.append("--seed-time=1")
        aria2_daemon_start_cmd.append("--split=10")
        aria2_daemon_start_cmd.append(f"--bt-stop-timeout=100")
        aria2_daemon_start_cmd.append(f"--max-tries=10")
        aria2_daemon_start_cmd.append(f"--retry-wait=2")
        #
        torlog.debug(aria2_daemon_start_cmd)
        #
        process = await asyncio.create_subprocess_exec(
            *aria2_daemon_start_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        torlog.debug(stdout)
        torlog.debug(stderr)
        arcli = await self._aloop.run_in_executor(None, partial(aria2p.Client, host="http://localhost", port=8100, secret=""))
        aria2 = await self._aloop.run_in_executor(None, aria2p.API, arcli)

        self._client = aria2
        return aria2

    async def execute(self):
        aria_instance = await self.get_client()
    
        
        if self._dl_link.lower().startswith("magnet:"):
            sagtus, err_message = await self.add_magnet(aria_instance, self._dl_link, self._new_file_name)
        
        elif self._dl_link.lower().endswith(".torrent"):
            #sagtus, err_message = await add_torrent(aria_instance, incoming_link)
            #sagtus, err_message = await add_url(aria_instance, incoming_link, c_file_name)
            self._is_errored = True
            self._error_reason = "Cant download this .torrent file"
            return False

        else:
            sagtus, err_message = await self.add_url()
        
        if not sagtus:
            self._is_errored = True
            self._error_reason = err_message
            return False
            
        torlog.info(err_message)
        self._gid = err_message

        op = await self.check_progress_for_dl()
        if self._dl_link.startswith("magnet:"):
            #
            err_message = await self.check_metadata()
            #
            await asyncio.sleep(1)
            if err_message is not None:
                op = await self.check_progress_for_dl()
            else:
                self._is_errored = True
                self._error_reason = "Can't get metadata.\n"
                return False
        await asyncio.sleep(1)
        
        
        
        if op:
            file = await self._aloop.run_in_executor(None, aria_instance.get_download, err_message)
            to_upload_file = file.name
            
            self.path = to_upload_file
            
            return to_upload_file
        else:
            return False

    async def check_progress_for_dl(self):
        aria2 = await self.get_client()
        gid = self._gid
        
        try:
            file = await self._aloop.run_in_executor(None, aria2.get_download, gid)
            
            complete = file.is_complete
            if not complete:
                if not file.error_message:             
                    self._update_info = file

                else:
                    self._is_errored = True
                    self._error_reason = file.error_message
                    torlog.error(f"The aria download faild due to this reason:- {file.error_message}")
                    return False
                await asyncio.sleep(get_val("EDIT_SLEEP_SECS"))
                
                # TODO idk not intrested in using recursion here
                return await self.check_progress_for_dl()
            else:
                self._is_completed = True
                self._is_done = True
                self._error_reason = f"Download completed: `{file.name}` - (`{file.total_length_string()}`)"
                
                return True

        except aria2p.client.ClientException as e:
            if " not found" in str(e) or "'file'" in str(e):
                fname = "N/A"
                try:
                    fname = file.name
                except:pass
                self._is_canceled = True
                self._error_reason = f"The Download was canceled. {fname}"
                return False
            else:
                torlog.warning("Errored due to ta client error.")
            pass

        except MessageNotModifiedError:
            pass
        
        except RecursionError:
            file.remove(force=True)
            self._is_errored = True
            self._error_reason = "The link is basically dead."
            return False

        except Exception as e:
            torlog.info(str(e))
            self._is_errored = True
            if " not found" in str(e) or "'file'" in str(e):
                self._error_reason = "The Download was canceled."
                return False
            else:
                torlog.exception(e)
                self._error_reason =  f"Error: {str(e)}"
                return False


    async def check_metadata(self):
        aria2 = await self.get_client()
        gid = self._gid

        file = await self._aloop.run_in_executor(None, aria2.get_download, gid)
        torlog.info(file)
        if not file.followed_by_ids:
            return None
        new_gid = file.followed_by_ids[0]
        torlog.info("Changing GID " + gid + " to " + new_gid)
        
        self._gid = new_gid

        return new_gid

    async def add_magnet(self, aria_instance, magnetic_link, c_file_name):
        try:
            download = await self._aloop.run_in_executor(None, aria_instance.add_magnet, magnetic_link)
        except Exception as e:
            return False, "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help"
        else:
            return True, "" + download.gid + ""

    async def add_torrent(self, aria_instance, torrent_file_path):
        if torrent_file_path is None:
            return False, "**FAILED** \n\nsomething wrongings when trying to add <u>TORRENT</u> file"
        if os.path.exists(torrent_file_path):
            # Add Torrent Into Queue
            try:

                download = await self._aloop.run_in_executor(None, partial(aria_instance.add_torrent, torrent_file_path, uris=None, options=None, position=None))

            except Exception as e:
                return False, "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help"
            else:
                return True, "" + download.gid + ""
        else:
            return False, "**FAILED** \nPlease try other sources to get workable link"
    
    async def add_url(self):
        aria_instance = await self.get_client()
        uris = [self._dl_link]
        dlp = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".", ""))
        os.makedirs(dlp, exist_ok=True)
        optis = {"dir":dlp}

        # Add URL Into Queue
        try:
            
            download = await self._aloop.run_in_executor(None, aria_instance.add_uris, uris, optis)

        except Exception as e:
            return False, "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help"
        else:
            return True, "" + download.gid + ""

    async def remove_dl(self, gid=None):
        if gid is None:
            gid = self._gid
        aria2 = await self.get_client()
        try:
            downloads = await self._aloop.run_in_executor(None, aria2.get_download, gid)
            downloads.remove(force=True, files=True)
        except:
            torlog.exception("exc")
            pass

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


class Aria2Controller:
    all_tasks = []
    def __init__(self, dl_link, user_msg, new_name=None):
        self._dl_link = dl_link
        self._user_msg = user_msg
        self._new_name = new_name

    async def execute(self):
        self._update_msg = await self._user_msg.reply("Starting the Aria2 Download.")

        self._aria2_down = Aria2Downloader(self._dl_link, self._user_msg.sender_id, self._new_name)
        self.all_tasks.append(self)
        # Status update active
        status_mgr = Aria2Status(self,self._aria2_down,self._user_msg.sender_id)
        StatusManager().add_status(status_mgr)
        status_mgr.set_active()

        res = await self._aria2_down.execute()

        # Status update inactive
        status_mgr.set_inactive()
        self.all_tasks.remove(self)

        if self._aria2_down.is_errored or self._aria2_down.is_canceled:
            await self._update_msg.edit("Your Task was unsccuessful. {}".format(self._aria2_down.get_error_reason()), buttons=None)
            return False
        else:
            if self._aria2_down.is_completed:
                await self._update_msg.edit(self._aria2_down.get_error_reason())    
            
            return res

    async def get_update_message(self):
        return self._update_msg
    
    async def get_downloader(self):
        return self._aria2_down