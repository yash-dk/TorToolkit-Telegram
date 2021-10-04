# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import re
import aiohttp
from requests.api import get
from telethon.tl.types import Config, Message, KeyboardButtonCallback, KeyboardButtonUrl
from telethon.errors import FloodWaitError, MessageNotModifiedError
from telethon import events
from ..utils.human_format import human_readable_bytes
from ..core.base_task import BaseTask
import asyncio, logging, os, time
import qbittorrentapi as qba
from functools import partial
from ..utils import hash_utils
from datetime import datetime
from ..core.getVars import get_val
from random import randint
from ..database.dbhandler import TorToolkitDB, TtkTorrents
from ..core.base_task import BaseTask
from ..status.qbittorrent_status import QbittorrentStatus
from ..status.status_manager import StatusManager

torlog = logging.getLogger(__name__)


class QbittorrentDownloader(BaseTask):


    def __init__(self, torrent, from_user_id, is_file = False):
        super().__init__()
        self._torrent = torrent

        self.from_user_id = from_user_id

        self._is_file = is_file
        self._client = None
        self._ext_hash = None
        self._files_finalized = False
        self._aloop = asyncio.get_event_loop()
        # This is a TG client
    
    def get_hash(self):
        return self._ext_hash

    async def get_client(self, host=None,port=None,uname=None,passw=None, retry=None) -> qba.TorrentsAPIMixIn:
        """Creates and returns a client to communicate with qBittorrent server. Max Retries 2
        """
        if self._client is not None:
            return self._client
        
        if retry is None:
            retry = get_val("QBIT_MAX_RETRIES")

        # Getting the connection
        host = host if host is not None else get_val("QBIT_HOST")
        port = port if port is not None else get_val("QBIT_PORT")
        uname = uname if uname is not None else get_val("QBIT_UNAME")
        passw = passw if passw is not None else get_val("QBIT_PASS")

        torlog.info(f"Trying to login in qBittorrent using creds {host} {port} {uname} {passw}")

        # Qbit client
        client = qba.Client(host=host,port=port,username=uname,password=passw)
        
        # Trying to connect to the server :)
        try:
            await self._aloop.run_in_executor(None,client.auth_log_in)
            torlog.info("Client connected successfully to the torrent server. :)")
            try:
                if get_val("ADD_CUSTOM_TRACKERS"):

                    url = get_val("TRACKER_SOURCE")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            tracker_data = await resp.text()
                else:
                    tracker_data = ""
                        
            except:
                tracker_data = ""

            qbaconf = {
                "disk_cache":20,
                "incomplete_files_ext":True,
                "max_connec":3000,
                "max_connec_per_torrent":300,
                "async_io_threads":6,
                "add_trackers_enabled":True,
                "add_trackers":tracker_data
            }
            
            await self._aloop.run_in_executor(None,client.application.set_preferences,qbaconf)
            torlog.debug("Setting the cache size to 20 incomplete_files_ext:True,max_connec:3000,max_connec_per_torrent:300,async_io_threads:6")
            self._client = client
            return client

        except qba.LoginFailed as e:
            torlog.exception("An errot occured invalid creds detected")
            return None

        except qba.APIConnectionError:
            if retry == 0:
                torlog.error("Tried to get the client 3 times no luck")
                return None
            
            torlog.info("Oddly enough the qbittorrent server is not running.... Attempting to start at port {}".format(port))
            cmd = f"qbittorrent-nox -d --webui-port={port}"
            cmd = cmd.split(" ")

            subpr = await asyncio.create_subprocess_exec(*cmd,stderr=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE)
            _, _ = await subpr.communicate()
            return await self.get_client(host,port,uname,passw,retry=retry-1)
    
    async def get_torrent_info(self, client=None, ext_hash=None):
        if client is None:
            client = await self.get_client()
        
        if ext_hash is None:
            if self._ext_hash is not None:
                ext_hash = self._ext_hash
        
        if ext_hash is None:
            return await self._aloop.run_in_executor(None,client.torrents_info)
        else:
            return await self._aloop.run_in_executor(None,partial(client.torrents_info,torrent_hashes=ext_hash))


    async def add_torrent_magnet(self):

        magnet = self._torrent

        """Adds a torrent by its magnet link.
        """    
        client = await self.get_client()
        try:
            ctor = len(await self.get_torrent_info(client))
            
            ext_hash = hash_utils.get_hash_magnet(magnet)
            # Set hash here
            self._ext_hash = ext_hash
            ext_res = await self.get_torrent_info(client, ext_hash)

            if len(ext_res) > 0:
                torlog.info(f"This torrent is in list {ext_res} {magnet} {ext_hash}")
                self._is_errored = True
                self._error_reason = "This torrent is already in the leech list."
                return False
            
            # hot fix for the below issue
            savepath = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".",""))
            op = await self._aloop.run_in_executor(None,partial(client.torrents_add, magnet, save_path=savepath))
            
            
            # TODO uncomment the below line and remove the above fix when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
            # op = client.torrents_add(magnet)

            # torrents_add method doesn't return anything so have to work around
            if op.lower() == "ok.":
                st = datetime.now()
                
                ext_res = await self.get_torrent_info(client, ext_hash)
                if len(ext_res) > 0:
                    torlog.info("Got torrent info from ext hash.")
                    return ext_res[0]

                while True:
                    if (datetime.now() - st).seconds >= 10:
                        torlog.warning("The provided torrent was not added and it was timed out. magnet was:- {}".format(magnet))
                        torlog.error(ext_hash)
                        
                        self._is_errored = True
                        self._error_reason = "The torrent was not added due to an error."

                        return False

                    # commenting in favour of wrong torrent getting returned
                    # ctor_new = client.torrents_info()
                    #if len(ctor_new) > ctor:
                    #    # https://t.me/c/1439207386/2977 below line is for this
                    #    torlog.info(ctor_new)
                    #    torlog.info(magnet)
                    #    return ctor_new[0]
                    
                    ext_res = await self.get_torrent_info(client, ext_hash)
                    if len(ext_res) > 0:
                        torlog.info("Got torrent info from ext hash.")
                        return ext_res[0]

            else:
                self._is_errored = True
                self._error_reason = "This is an unsupported/invalid link."

        except qba.UnsupportedMediaType415Error as e:
            #will not be used ever ;)
            torlog.error("Unsupported file was detected in the magnet here")
            self._is_errored = True
            self._error_reason = "This is an unsupported/invalid link."
            return False
        except Exception as e:
            torlog.exception("Error in adding torrent.")
            self._is_errored = True
            self._error_reason = "Error occured check logs."
            return False

    async def add_torrent_file(self):
        
        path = self._torrent

        if not os.path.exists(path):
            torlog.error("The path supplied to the torrent file was invalid.\n path:-{}".format(path))
            return False

        client = await self.get_client()
        try:

            ext_hash = hash_utils.get_hash_file(path)
            self._ext_hash = ext_hash
            ext_res = await self.get_torrent_info(client, ext_hash)

            if len(ext_res) > 0:
                torlog.info(f"This torrent is in list {ext_res} {path} {ext_hash}")
                self._is_errored = True
                self._error_reason = "This torrent is already in the leech list."
                return False
            
            # hot fix for the below issue
            savepath = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".",""))

            op = await self._aloop.run_in_executor(None,partial(client.torrents_add,torrent_files=[path], save_path=savepath))
            
            # TODO uncomment the below line and remove the above fix when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
            # op = client.torrents_add(torrent_files=[path])
            #this method doesn't return anything so have to work around
            
            if op.lower() == "ok.":
                st = datetime.now()
                
                await asyncio.sleep(2)
                
                ext_res = await self.get_torrent_info(client, ext_hash)
                if len(ext_res) > 0:
                    torlog.info("Got torrent info from ext hash.")
                    return ext_res[0]

                while True:
                    if (datetime.now() - st).seconds >= 20:
                        torlog.warning("The provided torrent was not added and it was timed out. file path was:- {}".format(path))
                        torlog.error(ext_hash)
                        self._is_errored = True
                        self._error_reason = "The torrent was not added due to an error."
                        return False
                    #ctor_new = client.torrents_info()
                    #if len(ctor_new) > ctor:
                    #    return ctor_new[0]
                    ext_res = await self.get_torrent_info(client, ext_hash)
                    if len(ext_res) > 0:
                        torlog.info("Got torrent info from ext hash.")
                        return ext_res[0]

            else:
                self._is_errored = True
                self._error_reason = "This is an unsupported/invalid link."
            
        except qba.UnsupportedMediaType415Error as e:
            # will not be used ever ;)
            torlog.error("Unsupported file was detected in the magnet here")
            self._is_errored = True
            self._error_reason = "This is an unsupported/invalid link."
            return False
        
        except Exception as e:
            torlog.exception("Error in adding torrent file.")
            self._is_errored = True
            self._error_reason = "Error occured check logs."
            return False

    async def pause_all(self):

        client = await self.get_client()
        await self._aloop.run_in_executor(None,partial(client.torrents_pause,torrent_hashes='all'))
        await asyncio.sleep(1)
        msg = ""
        tors = await self._aloop.run_in_executor(None,partial(client.torrents_info,status_filter="paused|stalled"))
        msg += "⏸️ Paused total <b>{}</b> torrents ⏸️\n".format(len(tors))

        for i in tors:
            if i.progress == 1:
                continue
            msg += "➡️<code>{}</code> - <b>{}%</b>\n".format(i.name,round(i.progress*100,2))

        return msg
        
    
    async def resume_all(self):

        client = await self.get_client()

        await self._aloop.run_in_executor(None,partial(client.torrents_resume, torrent_hashes='all'))

        await asyncio.sleep(1)
        msg = ""
        tors = await self._aloop.run_in_executor(None,partial(client.torrents_info,status_filter="stalled|downloading|stalled_downloading"))
        
        msg += "▶️Resumed {} torrents check the status for more...▶️".format(len(tors))

        for i in tors:
            if i.progress == 1:
                continue
            msg += "➡️<code>{}</code> - <b>{}%</b>\n".format(i.name,round(i.progress*100,2))

        return msg

    async def delete_all(self):

        client = await self.get_client()
        tors = await self.get_torrent_info(client)
        msg = "☠️ Deleted <b>{}</b> torrents.☠️".format(len(tors))
        client.torrents_delete(delete_files=True,torrent_hashes="all")

        return msg

    async def delete_this(self, ext_hash=None):
        "Mostly not a class method will be used separately."
        if ext_hash is None:
            if self._ext_hash is not None:
                ext_hash = self._ext_hash
            else:
                torlog.error("No ext hash found to delete.")
                return
        
        client = await self.get_client()
        await self._aloop.run_in_executor(None,partial(client.torrents_delete,delete_files=True,torrent_hashes=ext_hash))
        return True
    
    def progress_bar(percentage):
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

    async def deregister_torrent(self, ext_hash=None):
        "Mostly not a class method will be used separately. IG its a duplicate will be deprecated."

        if ext_hash is None:
            if self._ext_hash is not None:
                ext_hash = self._ext_hash
            else:
                torlog.error("No ext hash found to delete.")
                return
        
        client = await self.get_client()
        await self._aloop.run_in_executor(None,partial(client.torrents_delete, torrent_hashes=ext_hash,delete_files=True))
    
    async def register_torrent(self):
        client = await self.get_client()


        if not self._is_file:
            torlog.info(f"magnet :- {self._torrent}")
            torrent = await self.add_torrent_magnet()
            self._tor_info = torrent

            if isinstance(torrent,bool):
                return False
            torlog.info(torrent)

            if torrent.progress == 1 and torrent.completion_on > 1:
                self._is_errored = True
                self._error_reason = "The provided torrent was already completely downloaded."
                return False
            
        else:
            torrent = await self.add_torrent_file()
            self._tor_info = torrent
            
            if isinstance(torrent,bool):
                return False
            torlog.info(torrent)
            
            if torrent.progress == 1:
                self._is_errored = True
                self._error_reason = "The provided torrent was already completely downloaded."
                return False
            
    
    async def update_progress(self, except_retry=0, sleepsec=None):
        
        if sleepsec is None:
            sleepsec = get_val("EDIT_SLEEP_SECS")
        

        #switch to iteration from recursion as python doesn't have tailing optimization :O
        #RecursionError: maximum recursion depth exceeded
        
        is_meta = False
        meta_time = time.time()

        while True:
            tor_info = await self.get_torrent_info()
            #update cancellation
            print("refreshed")
            if len(tor_info) > 0:
                tor_info = tor_info[0]
                self._tor_info = tor_info
            else:
                self._is_canceled = True
                
                self._is_errored = True
                self._error_reason = "Torrent canceled ```{}``` "
                return False
            
            if tor_info.size > (get_val("MAX_TORRENT_SIZE") * 1024 * 1024 * 1024):
                self._is_errored = True
                self._error_reason = "Torrent oversized max size is {}. Try adding again and choose less files to download.".format(get_val("MAX_TORRENT_SIZE"))
                await self.delete_this(tor_info.hash)
                return False
            
            if self._files_finalized and get_val("TG_LEECH_FILE_LIMIT") != -1:
                # get file count with priority 1
                # which means they count to the total file count
                final_file_count = sum(1 for file in tor_info.files if file.priority == 1)
                if final_file_count > get_val("TG_LEECH_FILE_LIMIT"):
                    self._is_errored = True
                    self._error_reason = (
                        "Torrent exceeded file limit, max leech file limit is {}.".format(get_val("TG_LEECH_FILE_LIMIT"))
                        + " Try adding again and choose less files to download."
                    )
                    await self.delete_this(tor_info.hash)
                    return False

            try:

                if  tor_info.state == "metaDL":
                    is_meta = True
                else:
                    meta_time = time.time()
                    is_meta = False

                if (is_meta and (time.time() - meta_time) > get_val("TOR_MAX_TOUT")):
                    
                    self._is_errored = True
                    self._error_reason = "Torrent <code>{}</code> is DEAD. [Metadata Failed]".format(tor_info.name)
                    torlog.error("An torrent has no seeds clearing that torrent now. Torrent:- {} - {}".format(tor_info.hash,tor_info.name))
                    await self.delete_this(tor_info.hash)

                    return False

                try:
                    if tor_info.state == "error":

                        self._is_errored = True
                        self._error_reason = "Torrent <code>{}</code> errored out.".format(tor_info.name)
                        torlog.error("An torrent has error clearing that torrent now. Torrent:- {} - {}".format(tor_info.hash,tor_info.name))
                        await self.delete_this(tor_info.hash)
                        
                        return False
                    
                    #aio timeout have to switch to global something
                    await asyncio.sleep(sleepsec)

                    #stop the download when download complete
                    if tor_info.state == "uploading" or tor_info.state.lower().endswith("up"):
                        # this is to address the situations where the name would change abruptly
                        await self._aloop.run_in_executor(None,partial((await self.get_client()).torrents_pause,tor_info.hash))

                        # TODO uncomment the below line when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
                        # savepath = os.path.join(tor_info.save_path,tor_info.name)
                        # hot fix
                        try:
                            savepath = os.path.join(tor_info.save_path, os.listdir(tor_info.save_path)[-1])
                        except:
                            self._is_errored = True
                            self._error_reason = "Download path location failed"
                            
                            await self.delete_this(tor_info.hash)
                            return False

                        
                        
                        self._is_completed = True
                        self._error_reason = "Download completed: `{}` - (`{}`)\nTo path: `{}`".format(tor_info.name,human_readable_bytes(tor_info.total_size),tor_info.save_path)
                        self._is_done = True
                        return savepath
                    else:
                        #return await update_progress(client,message,torrent)
                        pass

                except (MessageNotModifiedError,FloodWaitError) as e:
                    torlog.error("{}".format(e))
                
            except Exception as e:
                torlog.exception("Something wrong is in update progress")
                
                self._is_errored = True
                self._error_reason = "Error occured {}".format(e)
                
                return False

    def cancel(self, is_admin=False):
        self._is_canceled = True
        if is_admin:
            self._canceled_by = self.ADMIN
        else: 
            self._canceled_by = self.USER
    
    async def get_update(self):
        return self._tor_info

    def get_error_reason(self):
        return self._error_reason


class QbitController:
    all_tasks = []
    def __init__(self, user_msg, entity_message, is_file = False, is_link = False):
        self._entity_msg = entity_message
        self._user_msg = user_msg
        self._is_file = is_file
        self._update_message = None
        self._is_link = is_link

    async def execute(self):
        
        if self._is_file:
            self._update_message = await self._user_msg.reply("Downloading the torrent file.")
            
            torrent = await self._entity_msg.download_media()
            self._qbit_task = QbittorrentDownloader(torrent, self._user_msg.sender_id, self._is_file)
            
            await self._qbit_task.register_torrent()

            if  self._qbit_task.is_errored:
                self._update_message("Your Task was unsccuessful. {}".format(self._qbit_task.get_error_reason()))
                return False
        
        elif self._is_link:
            self._update_message = await self._user_msg.reply("Downloading the torrent file.")
            torrent = ""
            async with aiohttp.ClientSession() as sess:
                async with sess.get(self._entity_msg.raw_text) as resp:
                    if resp.status == 200:
                        torrent = str(time.time()).replace(".","")+".torrent"
                        with open(torrent, "wb") as fi:
                            fi.write(await resp.read())
                    else:
                        await self._update_message.edit("Error got HTTP response code:- "+str(resp.status))
                        return False
            
            self._qbit_task = QbittorrentDownloader(torrent, self._user_msg.sender_id, self._is_link)
            
            await self._qbit_task.register_torrent()

            if  self._qbit_task.is_errored:
                self._update_message("Your Task was unsccuessful. {}".format(self._qbit_task.get_error_reason()))
                return False
        else:
            self._update_message = await self._user_msg.reply("Scanning the magnet link.")
            
            torrent = self.get_magnets(self._entity_msg.raw_text.strip())
            self._qbit_task = QbittorrentDownloader(torrent, self._user_msg.sender_id, self._is_file)

            await self._qbit_task.register_torrent()

            if  self._qbit_task.is_errored:
                await self._update_message.edit("Your Task was unsccuessful. {}".format(self._qbit_task.get_error_reason()))
                return False
            

        pincode = randint(1000,9999)
        db = TtkTorrents()

        torhash = self._qbit_task.get_hash()

        db.add_torrent(torhash, pincode)

        pincodetxt = f"getpin {torhash} {self._user_msg.sender_id}"
            
        data = "torcancel {} {}".format(torhash, self._user_msg.sender_id)
        base = get_val("BASE_URL_OF_BOT")

        urll = f"{base}/tortk/files/{torhash}"

        self._update_message = await self._update_message.edit("Download will be automatically started after 180s of no action.",buttons=[
            [
                KeyboardButtonUrl("Choose File from link",urll),
                KeyboardButtonCallback("Get Pincode",data=pincodetxt.encode("UTF-8"))
            ],
            [
                KeyboardButtonCallback("Done Selecting Files.",data=f"doneselection {self._user_msg.sender_id} {self._user_msg.id}".encode("UTF-8"))
            ]
        ])

        await self.get_confirm(self._user_msg)

        self._update_message = await self._update_message.edit(buttons=[KeyboardButtonCallback("Cancel Leech",data=data.encode("UTF-8"))])

        db.disable_torrent(torhash)
        self.all_tasks.append(self)
        # Status update active
        status_mgr = QbittorrentStatus(self, self._qbit_task, self._user_msg.sender_id)
        StatusManager().add_status(status_mgr)
        status_mgr.set_active()

        result = await self._qbit_task.update_progress()
        
        # Status update inactive
        self.all_tasks.remove(self)
        status_mgr.set_inactive()
        
        if self._qbit_task.is_errored or self._qbit_task.is_canceled:
            await self._update_message.edit("Your Task was unsccuessful. {}".format(self._qbit_task.get_error_reason()), buttons=None)
            return False
        else:
            if self._qbit_task.is_completed:
                await self._update_message.edit("{}".format(self._qbit_task.get_error_reason()), buttons=None)
            return result
        
    async def get_update_message(self):
        return self._update_message
    
    async def get_downloader(self):
        return self._qbit_task

    def get_magnets(self, text):
        matches = [ i for i in re.finditer("magnet:",text)]
        magnets = list()

        for i in range(len(matches)):
            if i == len(matches)-1:
                magnets.append(text[matches[i].span()[0]:])
            elif i == 0:
                magnets.append(text[:matches[i+1].span()[0]])
            else:
                magnets.append(text[matches[i].span()[0]:matches[i+1].span()[0]])

        for i in range(len(magnets)):
            magnets[i] = magnets[i].strip()

        return magnets[0]

    async def get_confirm(self, e):
        # abstract for getting the confirm in a context

        lis = [False,None,e.id]
        cbak = partial(self.get_confirm_callback,lis=lis)
        
        e.client.add_event_handler(
            #lambda e: test_callback(e,lis),
            cbak,
            events.CallbackQuery(pattern="doneselection")
        )

        start = time.time()

        while not lis[0]:
            if (time.time() - start) >= 180:
                break
            await asyncio.sleep(1)

        val = lis[1]
        
        e.client.remove_event_handler(cbak)

        # The files are finalized either by the user or it has been 180s
        self._qbit_task._files_finalized = True

        return val

    async def get_confirm_callback(self, e,lis):
        # handle the confirm callback
        data = e.data.decode("UTF-8")
        data = data.split(" ")
        o_sender = data[1]
        msgid = data[2]

        if o_sender != str(e.sender_id):
            await e.answer("Dont Touch it.......")
            return
        if str(lis[2]) != msgid:
            return
        await e.answer("Starting the download with the selected files.")
        lis[0] = True
        raise events.StopPropagation()