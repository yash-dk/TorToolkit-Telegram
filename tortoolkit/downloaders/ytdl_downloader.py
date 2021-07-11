# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import asyncio,shlex,logging,time,os,aiohttp,shutil
import json, time, asyncio
from telethon.hints import MessageLike
from telethon import events
from telethon.tl.types import KeyboardButtonCallback, KeyboardButtonUrl
from typing import Union,List,Tuple,Dict,Optional
from ..utils.human_format import human_readable_bytes
from ..core.getVars import get_val
from ..uploaders.rclone_uploader import RcloneUploader
from ..core.base_task import BaseTask
from functools import partial
from PIL import Image

torlog = logging.getLogger(__name__)

# attempt to decorate error prone areas
import traceback
def skipTorExp(func):
    def wrap_func(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception as e:
            torlog.error(e)
            return
    return wrap_func

async def cli_call(cmd: Union[str,List[str]]) -> Tuple[str,str]:
    if isinstance(cmd,str):
        cmd = shlex.split(cmd)
    elif isinstance(cmd,(list,tuple)):
        pass
    else:
        return None,None
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stderr=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()

    with open("test.txt","w",encoding="UTF-8") as f:
        f.write(stdout)
    
    return stdout, stderr


async def get_yt_link_details(url: str) -> Union[Dict[str,str], None]:
    cmd = "youtube-dl --no-warnings --youtube-skip-dash-manifest --dump-json"
    cmd = shlex.split(cmd)
    if "hotstar" in url:
        cmd.append("--geo-bypass-country")
        cmd.append("IN")
    cmd.append(url)
    
    out, error = await cli_call(cmd)
    if error:
        torlog.error(f"Error occured:- {error} for url {url}")
    # sanitize the json
    out = out.replace("\n",",")
    out = "[" + out + "]"
    try:
        return json.loads(out)[0], None
    except:
        torlog.exception("Error occured while parsing the json.\n")
        return None, error

async def get_max_thumb(data: dict, suid: str) -> str:
    thumbnail = data.get("thumbnail")
    thumb_path = None

    # alot of context management XD
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                thumb_path = os.path.join(os.getcwd(),"userdata")
                if not os.path.exists(thumb_path):
                    os.mkdir(thumb_path)

                thumb_path = os.path.join(thumb_path,f"{suid}.webp")
                with open(thumb_path,"wb") as ifile:
                    ifile.write(await resp.read())

        Image.open(thumb_path).convert("RGB").save(thumb_path)

        return thumb_path
    except:
        torlog.exception("Error in thumb gen")
        return None

async def create_quality_menu(url: str,message: MessageLike, message1: MessageLike, dest: str,jsons: Optional[str] = None, suid: Optional[str] = None):
    if jsons is None:
        data, err = await get_yt_link_details(url)
        suid = str(time.time()).replace(".","")
    else:
        data = jsons

    #with open("test.txt","w") as f:
    #    f.write(json.dumps(data))

    if data is None:
        return None, err
    else:
        unique_formats = dict()
        for i in data.get("formats"):
            c_format = i.get("format_note")
            if c_format is None:
                c_format = i.get("height")
            if not c_format in unique_formats:
                if i.get("filesize") is not None:
                    unique_formats[c_format] = [i.get("filesize"),i.get("filesize")]
                else:
                    unique_formats[c_format] = [0,0]

            else:
                if i.get("filesize") is not None:
                    if unique_formats[c_format][0] > i.get("filesize"):
                        unique_formats[c_format][0] = i.get("filesize")
                    else:
                        unique_formats[c_format][1] = i.get("filesize")

        buttons = list()
        for i in unique_formats.keys():
            
            # add human bytes here
            if i == "tiny":
                text = f"tiny [{human_readable_bytes(unique_formats[i][0])} - {human_readable_bytes(unique_formats[i][1])}] ➡️"
                cdata = f"ytdlsmenu|{i}|{message1.sender_id}|{suid}|{dest}" # add user id
            else:
                text = f"{i} [{human_readable_bytes(unique_formats[i][0])} - {human_readable_bytes(unique_formats[i][1])}] ➡️"
                cdata = f"ytdlsmenu|{i}|{message1.sender_id}|{suid}|{dest}" # add user id
            buttons.append([KeyboardButtonCallback(text,cdata.encode("UTF-8"))])
        buttons.append([KeyboardButtonCallback("Audios ➡️",f"ytdlsmenu|audios|{message1.sender_id}|{suid}|{dest}")])
        await message.edit("Choose a quality/option available below.",buttons=buttons)
        
        if jsons is None:
            path = os.path.join(os.getcwd(),'userdata')
            
            if not os.path.exists(path):
                os.mkdir(path)
            
            path = os.path.join(path,f"{suid}.json")
            
            with open(path,"w",encoding="UTF-8") as file:
                file.write(json.dumps(data))



    return True,None
        
async def handle_ytdl_command(e: MessageLike):
    # Initial Menu buildup for yt-dl
    if not e.is_reply:
        await e.reply("Reply to a youtube video link.")
        return
    msg = await e.get_reply_message()

    tsp = time.time()
    buts = [[KeyboardButtonCallback("To Telegram",data=f"ytdlselect tg {tsp}")]]
    if await RcloneUploader(None, None).get_config() is not None:
        buts.append(
            [KeyboardButtonCallback("To Drive",data=f"ytdlselect drive {tsp}")]
        )

    msg1 = await e.reply(f"Processing the given link......\nChoose destination. Default destination will be chosen in {get_val('DEFAULT_TIMEOUT')}.", buttons=buts)
    
    choice = await get_ytdl_choice(e,tsp)
    msg1 = await msg1.edit("Processing the given link.......",buttons=None)
    await asyncio.sleep(1)

    if msg.text.find("http") != -1:
        res, err = await create_quality_menu(msg.text.strip(),msg1,msg, choice)
        if res is None:
            await msg1.edit(f"<code>Invalid link provided.\n{err}</code>",parse_mode="html")
    else:
        await e.reply("Invalid link provided.")

async def handle_ytdl_callbacks(e: MessageLike):
    # This is used to handle the menu clicked by the user.
    # ytdlsmenu | format | sender_id | suid | dest
    data = e.data.decode("UTF-8")
    data = data.split("|")
    
    if data[0] == "ytdlsmenu":
        if data[2] != str(e.sender_id):
            await e.answer("Not valid user, Dont touch.")
            return
        
        path = os.path.join(os.getcwd(),'userdata',data[3]+".json")
        if os.path.exists(path):
            with open(path) as file:
                ytdata = json.loads(file.read())
                buttons = list()
                if data[1] == "audios":
                    for i in ["64K","128K","320K"]:
                        text = f"{i} [MP3]"
                        cdata = f"ytdldfile|{i}|{e.sender_id}|{data[3]}|{data[4]}"
                        buttons.append([KeyboardButtonCallback(text,cdata.encode("UTF-8"))])
                else:
                    j = 0
                    for i in ytdata.get("formats"):
                        c_format = i.get("format_note")
                        format_id = i.get('format_id')
                        height = i.get('format')
                        if c_format is None:
                            c_format = str(i.get("height"))
                            format_id = f"xxother{j}"
                            height = i.get('format')
                        if not c_format == data[1]:
                            continue
                        
                        
                        if not height:
                            continue
                            
                        text = f"{height} [{i.get('ext')}] [{human_readable_bytes(i.get('filesize'))}] {str(i.get('vcodec'))}"
                        cdata = f"ytdldfile|{format_id}|{e.sender_id}|{data[3]}|{data[4]}"
                        
                        buttons.append([KeyboardButtonCallback(text,cdata.encode("UTF-8"))])
                        j+=1
                
                buttons.append([KeyboardButtonCallback("Go Back 😒",f"ytdlmmenu|{data[2]}|{data[3]}|{data[4]}")])
                await e.edit(f"Files for quality {data[1]}, at the end it is the Video Codec. Mostly prefer the last one with you desired extension if you want streamable video. Try rest if you want.",buttons=buttons)
                


        else:
            await e.answer("Try again something went wrong.",alert=True)
            await e.delete()
    elif data[0] == "ytdlmmenu":
        if data[1] != str(e.sender_id):
            await e.answer("Not valid user, Dont touch.")
            return
        path = os.path.join(os.getcwd(),'userdata',data[2]+".json")
        if os.path.exists(path):
            with open(path,encoding="UTF-8") as file:
                ytdata = json.loads(file.read())
                await create_quality_menu("",await e.get_message(),e,data[3],ytdata,data[2])

        else:
            await e.answer("Try again something went wrong.",alert=True)
            await e.delete()

async def handle_ytdl_playlist(e: MessageLike) -> None:
    if not e.is_reply:
        await e.reply("Reply to a youtube playlist link.")
        return
    url = await e.get_reply_message()
    url = url.text.strip()
    cmd = f"youtube-dl -i --flat-playlist --dump-single-json {url}"
    
    tsp = time.time()
    buts = [[KeyboardButtonCallback("To Telegram",data=f"ytdlselect tg {tsp}")]]
    if await RcloneUploader(None, None).get_config() is not None:
        buts.append(
            [KeyboardButtonCallback("To Drive",data=f"ytdlselect drive {tsp}")]
        )

    msg = await e.reply(f"Processing your Youtube Playlist download request.\nChoose destination. Default destination will be chosen in {get_val('DEFAULT_TIMEOUT')}.",buttons=buts)

    choice = await get_ytdl_choice(e,tsp) #blocking call
    msg = await msg.edit("Processing your Youtube Playlist download request.",buttons=None)
    await asyncio.sleep(1)

    # cancel the playlist if time exceed 5 mins
    try:
        out, err = await asyncio.wait_for(cli_call(cmd),300)
    except asyncio.TimeoutError:
        await msg.edit("Processing time exceeded... The playlist seem to long to be worked with 😢\n If the playlist is short and you think its error report back.")
        return
    
    if err:
        await msg.edit(f"Failed to load the playlist with the error:- <code>{err}</code>",parse_mode="html")
        return
    

    try:
        pldata = json.loads(out)
        entities = pldata.get("entries")
        if len(entities) <= 0:
            await msg.edit("Cannot load the videos from this playlist ensure that the playlist is not <code>'My Mix or Mix'</code>. It shuold be a public or unlisted youtube playlist.")
            return

        entlen = len(entities)
        keybr = list()
        
        # limit the max vids
        if entlen > get_val("MAX_YTPLAYLIST_SIZE"):

            await msg.edit(f"Playlist too large max {get_val('MAX_YTPLAYLIST_SIZE')} vids allowed as of now. This has {entlen}")
            return


        # format> ytdlplaylist | quality | suid | sender_id
        suid = str(time.time()).replace(".","")

        for i in ["144","240","360","480","720","1080","1440","2160"]:
            keybr.append([KeyboardButtonCallback(text=f"{i}p All videos",data=f"ytdlplaylist|{i}|{suid}|{e.sender_id}|{choice}")])

        keybr.append([KeyboardButtonCallback(text=f"Best All videos",data=f"ytdlplaylist|best|{suid}|{e.sender_id}|{choice}")])
        
        
        keybr.append([KeyboardButtonCallback(text="Best all audio only. [340k]",data=f"ytdlplaylist|320k|{suid}|{e.sender_id}|{choice}")])
        keybr.append([KeyboardButtonCallback(text="Medium all audio only. [128k]",data=f"ytdlplaylist|128k|{suid}|{e.sender_id}|{choice}")])
        keybr.append([KeyboardButtonCallback(text="Worst all audio only. [64k]",data=f"ytdlplaylist|64k|{suid}|{e.sender_id}|{choice}")])

        await msg.edit(f"Found {entlen} videos in the playlist.",buttons=keybr) 

        path = os.path.join(os.getcwd(),'userdata')
        
        if not os.path.exists(path):
            os.mkdir(path)
        
        path = os.path.join(path,f"{suid}.json")
        
        with open(path,"w",encoding="UTF-8") as file:
            file.write(json.dumps(pldata))

    except:
        await msg.edit("Failed to parse the playlist. Check log if you think its error.")
        torlog.exception("Playlist Parse failed") 

async def get_ytdl_choice(e,timestamp):
    # abstract for getting the confirm in a context

    lis = [False,None]
    cbak = partial(get_leech_choice_callback,o_sender=e.sender_id,lis=lis,ts=timestamp)
    
    e.client.add_event_handler(
        #lambda e: test_callback(e,lis),
        cbak,
        events.CallbackQuery(pattern="ytdlselect")
    )

    start = time.time()
    defleech = get_val("DEFAULT_TIMEOUT")

    while not lis[0]:
        if (time.time() - start) >= 60: #TIMEOUT_SEC:
            
            if defleech == "leech":
                return "tg"
            elif defleech == "rclone":
                return "drive"
            else:
                # just in case something goes wrong
                return "tg"
            break
        await asyncio.sleep(1)

    val = lis[1]
    
    e.client.remove_event_handler(cbak)

    return val

async def get_leech_choice_callback(e,o_sender,lis,ts):
    # handle the confirm callback

    if o_sender != e.sender_id:
        return
    data = e.data.decode().split(" ")
    if data [2] != str(ts):
        return
    
    lis[0] = True
    
    lis[1] = data[1]


class YTDLDownloader(BaseTask):
    def __init__(self, fromat_id, sender_id, suid):
        super().__init__()
        self._format_id = fromat_id
        self._sender_id = sender_id
        self._suid = suid

    async def execute(self):
        # ytdldfile | format_id | sender_id | suid | dest
        #       0       1           2           3     4

        is_audio = False

        path = os.path.join(os.getcwd(),'userdata',self._suid+".json")
        if os.path.exists(path):
            with open(path,encoding="UTF-8") as file:
                ytdata = json.loads(file.read())
                yt_url = ytdata.get("webpage_url")
                thumb_path = await get_max_thumb(ytdata,self._suid)

                op_dir = os.path.join(os.getcwd(),'userdata',self._suid)
                
                os.makedirs(op_dir, exist_ok=True)
                
                if self._format_id.startswith("xxother"):
                    self._format_id = self._format_id.replace("xxother","")
                    self._format_id = int(self._format_id)
                    j = 0
                    for i in ytdata.get("formats"):
                        if j == self._format_id:
                            self._format_id = i.get("format_id")
                        j +=1
                else:
                    for i in ytdata.get("formats"):
                        if i.get("format_id") == self._format_id:
                            print(i)
                            if i.get("acodec") is not None:
                                if "none" not in i.get("acodec"):
                                    is_audio = True
                                
                        
                if self._format_id.endswith("K"):
                    cmd = f"youtube-dl -i --extract-audio --add-metadata --audio-format mp3 --audio-quality {self._format_id} -o '{op_dir}/%(title)s.%(ext)s' {yt_url}"

                else:
                    if is_audio:
                        cmd = f"youtube-dl --continue --embed-subs --no-warnings --hls-prefer-ffmpeg --prefer-ffmpeg -f {self._format_id} -o {op_dir}/%(title)s.%(ext)s {yt_url}"
                    else:
                        cmd = f"youtube-dl --continue --embed-subs --no-warnings --hls-prefer-ffmpeg --prefer-ffmpeg -f {self._format_id}+bestaudio[ext=m4a]/best -o {op_dir}/%(title)s.%(ext)s {yt_url}"
                
                out, err = await cli_call(cmd)
                
                if not err:
                    
                    # TODO Fix the original thumbnail
                    # rdict = await upload_handel(op_dir,await e.get_message(),e.sender_id,dict(),thumb_path=thumb_path)
                    
                    self._is_completed = True
                    self._is_done = True

                    return op_dir
                else:
                    torlog.error(err)
                    
                    if "HTTP Error 429" in err:
                        emsg = "HTTP Error 429: Too many requests try after a while."
                    else:
                        emsg = "An error has occured trying to upload any files that are found here."
                    
                    self._is_errored = True
                    self._error_reason = emsg
                
                    return op_dir

        else:
            self._is_errored = True
            self._error_reason = "Try again something went wrong."
            return False


class YTDLController:
    def __init__(self, callback, user_message):
        self.callback = callback
        self.user_message = user_message
    
    async def execute(self):
        # ytdldfile | format_id | sender_id | suid | dest
        data = self.callback.data.decode("UTF-8")
        data = data.split("|")

        if data[2] != str(self.callback.sender_id):
            await self.callback.answer("Not valid user, Dont touch.")
            return False
        else:
            await self.callback.answer("Crunching Data.....")

        await self.callback.edit(buttons=None)

        ytdl_task = YTDLDownloader(data[1],data[2],data[3])
        res = await ytdl_task.execute()

        if ytdl_task.is_errored:
            if res is False:
                omess = await self.user_message.get_reply_message()
                await self.user_message.edit("Something went wrong, try again later."+str(ytdl_task.get_error_reason()))
                await self.omess.reply("Something went wrong, try again later."+str(ytdl_task.get_error_reason()))

                return res
            else:
                return res
        else:
            return res


class PYTDLDownloader(BaseTask):
    def __init__(self, quality, sender_id, suid):
        super().__init__()
        self._quality = quality
        self._sender_id = sender_id
        self._suid = suid
    
    # ytdlplaylist | quality | suid | sender_id | choice(tg/drive)
    #   0               1          2       3           4    

    async def execute(self):

        path = os.path.join(os.getcwd(),"userdata",self._suid+".json")
        if os.path.exists(path):
            opdir = os.path.join(os.getcwd(),"userdata",self._suid)
            if not os.path.exists(opdir):
                os.mkdir(opdir)

            with open(path) as file:
                pldata = json.loads(file.read())
            url = pldata.get("webpage_url")

            if self._quality.endswith("k"):
                audcmd = f"youtube-dl -i --extract-audio --add-metadata --audio-format mp3 --audio-quality {self._quality} -o '{opdir}/%(playlist_index)s - %(title)s.%(ext)s' {url}"
                out, err = await cli_call(audcmd)

                ofiles = len(os.listdir(opdir))

                if err and ofiles < 2 :
                    self._is_errored = True
                    self._error_reason = f"Failed to download the audios <code>{err}</code>"
                else:
                    if err:
                        self._is_errored = True
                        self._error_reason = "Some videos from this have errored in download. Uploading which are successfull."
                    
                return opdir
                    
            else:
                print("here i am bot")
                if self._quality == "best":
                    vidcmd = f"youtube-dl -i --continue --embed-subs --no-warnings --prefer-ffmpeg -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best' -o '{opdir}/%(playlist_index)s - %(title)s.%(ext)s' {url}"
                else:
                    vidcmd = f"youtube-dl -i --continue --embed-subs --no-warnings --prefer-ffmpeg -f 'bestvideo[ext=mp4,height<={self._quality}]+bestaudio[ext=m4a]/best' -o '{opdir}/%(playlist_index)s - %(title)s.%(ext)s' {url}"
                out, err = await cli_call(vidcmd)
                
                ofiles = len(os.listdir(opdir))

                if err and ofiles < 2 :
                    self._is_errored = True
                    self._error_reason = f"Failed to download the videos <code>{err}</code>"
                else:
                    if err:
                        self._is_errored = True
                        self._error_reason = "Some videos from this have errored in download. Uploading which are successfull."
                    
                    return opdir
            
        else:
            self._is_errored = True
            self._error_reason = "Something went wrong try again."
            torlog.error("the file for that suid was not found.")

class PYTDLController:
    def __init__(self, callback, user_message):
        self.callback = callback
        self.user_message = user_message
    
    async def execute(self):
        # ytdlplaylist | quality | suid | sender_id | choice(tg/drive)
        data = self.callback.data.decode("UTF-8")
        data = data.split("|")

        if data[3] != str(self.callback.sender_id):
            await self.callback.answer("Not valid user, Dont touch.")
            return False
        else:
            await self.callback.answer("Crunching Data.....")

        await self.callback.edit(buttons=None)

        ytdl_task = PYTDLDownloader(data[1],data[3],data[2])
        res = await ytdl_task.execute()
        print("sdsdsdds",res, ytdl_task.get_error_reason())
        if ytdl_task.is_errored:
            if res is False:
                omess = await self.user_message.get_reply_message()
                await self.user_message.edit("Something went wrong, try again later."+str(ytdl_task.get_error_reason()))
                await self.omess.reply("Something went wrong, try again later."+str(ytdl_task.get_error_reason()))

                return res
            else:
                return res
        else:
            return res

#todo
# Add the YT playlist feature here
# Add the YT channels feature here 