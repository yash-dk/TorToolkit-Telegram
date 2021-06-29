from telethon.tl.types import Config
from ..core.base_task import BaseTask
import asyncio, logging, os, time
import qbittorrentapi as qba
from functools import partial
from ..utils import hash_utils
from datetime import datetime
from ..core.getVars import get_val
torlog = logging.getLogger(__name__)


class QbittorrentDownloader:


    def __init__(self):
        self._aloop = asyncio.get_event_loop()
        self._client = None
    
    async def get_client(self, host=None,port=None,uname=None,passw=None,retry=2) -> qba.TorrentsAPIMixIn:
        """Creats and returns a client to communicate with qBittorrent server. Max Retries 2
        """
        if self._client is not None:
            return self._client
        
        # Getting the connection
        host = host if host is not None else "localhost"
        port = port if port is not None else "8090"
        uname = uname if uname is not None else "admin"
        passw = passw if passw is not None else "adminadmin"
        torlog.info(f"Trying to login in qBittorrent using creds {host} {port} {uname} {passw}")

        client = qba.Client(host=host,port=port,username=uname,password=passw)
        
        # Trying to connect to the server :)
        try:
            await self._aloop.run_in_executor(None,client.auth_log_in)
            torlog.info("Client connected successfully to the torrent server. :)")
            
            qbaconf = {
                "disk_cache":20,
                "incomplete_files_ext":True,
                "max_connec":3000,
                "max_connec_per_torrent":300,
                "async_io_threads":6
            }
            
            await self._aloop.run_in_executor(None,client.application.set_preferences,qbaconf)
            torlog.debug("Setting the cache size to 20 incomplete_files_ext:True,max_connec:3000,max_connec_per_torrent:300,async_io_threads:6")
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
    
    async def get_torrent_info(self, client, ehash=None):

        if ehash is None:
            return await self._aloop.run_in_executor(None,client.torrents_info)
        else:
            return await self._aloop.run_in_executor(None,partial(client.torrents_info,torrent_hashes=ehash))


    async def add_torrent_magnet(self, magnet,message):
        """Adds a torrent by its magnet link.
        """    
        client = await self.get_client()
        try:
            ctor = len(await self.get_torrent_info(client))
            
            ext_hash = hash_utils.get_hash_magnet(magnet)
            ext_res = await self.get_torrent_info(client, ext_hash)

            if len(ext_res) > 0:
                torlog.info(f"This torrent is in list {ext_res} {magnet} {ext_hash}")
                await message.edit("This torrent is alreaded in the leech list.")
                return False
            # hot fix for the below issue
            savepath = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".",""))
            op = await self.aloop.run_in_executor(None,partial(client.torrents_add, magnet, save_path=savepath))
            
            
            # TODO uncomment the below line and remove the above fix when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
            # op = client.torrents_add(magnet)

            # torrents_add method dosent return anything so have to work around
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
                        await message.edit("The torrent was not added due to an error.")
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
                await message.edit("This is an unsupported/invalid link.")

        except qba.UnsupportedMediaType415Error as e:
            #will not be used ever ;)
            torlog.error("Unsupported file was detected in the magnet here")
            await message.edit("This is an unsupported/invalid link.")
            return False
        except Exception as e:
            torlog.exception("Error in adding torrent.")
            await message.edit("Error occured check logs.")
            return False

    async def add_torrent_file(self, path, message):
        if not os.path.exists(path):
            torlog.error("The path supplied to the torrent file was invalid.\n path:-{}".format(path))
            return False

        client = await self.get_client()
        try:

            ext_hash = hash_utils.get_hash_file(path)
            ext_res = await self.get_torrent_info(client, ext_hash)

            if len(ext_res) > 0:
                torlog.info(f"This torrent is in list {ext_res} {path} {ext_hash}")
                await message.edit("This torrent is alreaded in the leech list.")
                return False
            
            # hot fix for the below issue
            savepath = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".",""))

            op = await self.aloop.run_in_executor(None,partial(client.torrents_add,torrent_files=[path], save_path=savepath))
            
            # TODO uncomment the below line and remove the above fix when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
            # op = client.torrents_add(torrent_files=[path])
            #this method dosent return anything so have to work around
            
            if op.lower() == "ok.":
                st = datetime.now()
                #ayehi wait karna hai
                await asyncio.sleep(2)
                
                ext_res = await self.get_torrent_info(client, ext_hash)
                if len(ext_res) > 0:
                    torlog.info("Got torrent info from ext hash.")
                    return ext_res[0]

                while True:
                    if (datetime.now() - st).seconds >= 20:
                        torlog.warning("The provided torrent was not added and it was timed out. file path was:- {}".format(path))
                        torlog.error(ext_hash)
                        await message.edit("The torrent was not added due to an error.")
                        return False
                    #ctor_new = client.torrents_info()
                    #if len(ctor_new) > ctor:
                    #    return ctor_new[0]
                    ext_res = await self.get_torrent_info(client, ext_hash)
                    if len(ext_res) > 0:
                        torlog.info("Got torrent info from ext hash.")
                        return ext_res[0]

            else:
                await message.edit("This is an unsupported/invalid link.")
            
        except qba.UnsupportedMediaType415Error as e:
            # will not be used ever ;)
            torlog.error("Unsupported file was detected in the magnet here")
            await message.edit("This is an unsupported/invalid link.")
            return False
        
        except Exception as e:
            torlog.exception("Error in adding torrent file.")
            await message.edit("Error occured check logs.")
            return False

    async def pause_all(self, message):
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

        await message.reply(msg,parse_mode="html")
        await message.delete()
    
    async def resume_all(self, message):
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

        await message.reply(msg,parse_mode="html")
        await message.delete()

    async def delete_all(self, message):
        client = await self.get_client()
        tors = await self.get_torrent_info(client)
        msg = "☠️ Deleted <b>{}</b> torrents.☠️".format(len(tors))
        client.torrents_delete(delete_files=True,torrent_hashes="all")

        await message.reply(msg,parse_mode="html")
        await message.delete()

    async def delete_this(self, ext_hash):
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

    async def deregister_torrent(self, hashid):
        client = await self.get_client()
        await self._aloop.run_in_executor(None,partial(client.torrents_delete, torrent_hashes=hashid,delete_files=True))