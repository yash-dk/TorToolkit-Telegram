import asyncio,shlex,logging,time,os,aiohttp,shutil
import orjson as json
from telethon.hints import MessageLike
from telethon.tl.types import KeyboardButtonCallback
from typing import Union,List,Tuple,Dict,Optional
from ..functions.Human_Format import human_readable_bytes
from ..functions.tele_upload import upload_handel
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
    cmd.append(url)
    
    out, error = await cli_call(cmd)
    if error:
        torlog.error(f"Error occured:- {error} for url {url}")
    
    try:
        return json.loads(out)
    except:
        torlog.exception("Error occured while parsing the json.\n")
        return None 

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

async def create_quality_menu(url: str,message: MessageLike, message1: MessageLike,jsons: Optional[str] = None, suid: Optional[str] = None):
    if jsons is None:
        data = await get_yt_link_details(url)
        suid = str(time.time()).replace(".","")
    else:
        data = jsons

    with open("test.txt","w") as f:
        f.write(json.dumps(data).decode("UTF-8"))

    if data is None:
        return None
    else:
        unique_formats = dict()
        for i in data.get("formats"):
            c_format = i.get("format_note")
            if not c_format in unique_formats:
                unique_formats[c_format] = [i.get("filesize"),i.get("filesize")]
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
                text = f"tiny/audios [{human_readable_bytes(unique_formats[i][0])} - {human_readable_bytes(unique_formats[i][1])}] ➡️"
                cdata = f"ytdlsmenu|{i}|{message1.sender_id}|{suid}" # add user id
            else:
                text = f"{i} [{human_readable_bytes(unique_formats[i][0])} - {human_readable_bytes(unique_formats[i][1])}] ➡️"
                cdata = f"ytdlsmenu|{i}|{message1.sender_id}|{suid}" # add user id
            buttons.append([KeyboardButtonCallback(text,cdata.encode("UTF-8"))])
        
        await message.edit("Choose a quality/option available below.",buttons=buttons)
        
        if jsons is None:
            path = os.path.join(os.getcwd(),'userdata')
            
            if not os.path.exists(path):
                os.mkdir(path)
            
            path = os.path.join(path,f"{suid}.json")
            
            with open(path,"w",encoding="UTF-8") as file:
                file.write(json.dumps(data).decode("UTF-8"))



    return True
        
async def handle_ytdl_command(e: MessageLike):
    msg = await e.get_reply_message()
    msg1 = await e.reply("Processing the given link.....")
    if msg.text.find("http") != -1:
        res = await create_quality_menu(msg.text.strip(),msg1,msg)
        if res is None:
            await msg1.edit("Invalid link provided.")
    else:
        await e.reply("Invalid link provided.")

async def handle_ytdl_callbacks(e: MessageLike):
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
                for i in ytdata.get("formats"):
                    
                    c_format = i.get("format_note")
                    if not c_format == data[1]:
                        continue
                    text = f"{i.get('format')} [{human_readable_bytes(i.get('filesize'))}]"
                    cdata = f"ytdldfile|{i.get('format_id')}|{e.sender_id}|{data[3]}"
                    buttons.append([KeyboardButtonCallback(text,cdata.encode("UTF-8"))])
                
                buttons.append([KeyboardButtonCallback("Go Back 😒",f"ytdlmmenu|{data[2]}|{data[3]}")])
                await e.edit(f"Files for quality {data[1]}",buttons=buttons)
                


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
                await create_quality_menu("",await e.get_message(),e,ytdata,data[2])

        else:
            await e.answer("Try again something went wrong.",alert=True)
            await e.delete()

async def handle_ytdl_file_download(e: MessageLike, queue: asyncio.Queue):
    # ytdldfile | format_id | sender_id | suid
    data = e.data.decode("UTF-8")
    data = data.split("|")
    
    if data[2] != str(e.sender_id):
        await e.answer("Not valid user, Dont touch.")
        return
    else:
        await e.answer("Crunching Data.....")
    
    path = os.path.join(os.getcwd(),'userdata',data[3]+".json")
    if os.path.exists(path):
        with open(path,encoding="UTF-8") as file:
            ytdata = json.loads(file.read())
            yt_url = ytdata.get("webpage_url")
            thumb_path = await get_max_thumb(ytdata,data[3])

            op_dir = os.path.join(os.getcwd(),'userdata',data[3])
            if not os.path.exists(op_dir):
                os.mkdir(op_dir)

            cmd = f"youtube-dl --continue --embed-subs --no-warnings --prefer-ffmpeg -f {data[1]} -o {op_dir}/%(title)s.%(ext)s {yt_url}"
            out, err = await cli_call(cmd)
            print(out,"  -  ",err)
            if not err:
                
                await upload_handel(op_dir,await e.get_message(),e.sender_id,dict(),queue=queue,thumb_path=thumb_path)
                
                
                shutil.rmtree(op_dir)
                os.remove(thumb_path)
                os.remove(path)

    else:
        await e.answer("Try again something went wrong.",alert=True)
        await e.delete()

async def handle_ytdl_playlist(e: MessageLike) -> None:
    url = await e.get_reply_message()
    url = url.text.strip()
    cmd = f"youtube-dl -i --flat-playlist --dump-single-json {url}"
    
    msg = await e.reply("Processing your Youtube Playlist download request")

    # cancel the playlist if time exceed 3 mins
    try:
        out, err = await asyncio.wait_for(cli_call(cmd),180)
    except asyncio.TimeoutError:
        await msg.edit("Processing time exceeded... The playlist seem to long to be worked with 😢\n If the playlist is short and you think its error report back.")
        return
    
    if err:
        await msg.edit(f"Failed to load the playlist with the error:- <code>{err}</code>",parse_mode="html")
        return
    
    print(cmd)

    try:
        pldata = json.loads(out)
        entities = pldata.get("entries")
        if len(entities) <= 0:
            await msg.edit("Cannot load the videos from this playlist ensure that the playlist is not <code>'My Mix or Mix'</code>. It shuold be a public or unlisted youtube playlist.")
            return

        entlen = len(entities)
        keybr = list()
        
        # format> ytdlplaylist | quality | suid
        suid = str(time.time()).replace(".","")

        for i in ["144","240","360","480","720","1080","1440","2160"]:
            keybr.append([KeyboardButtonCallback(text=f"{i}p All videos",data=f"ytdlplaylist|{i}|{suid}")])

        keybr.append([KeyboardButtonCallback(text=f"Best All videos",data=f"ytdlplaylist|best|{suid}")])
        
        await msg.edit(f"Found {entlen} videos in the playlist.",buttons=keybr) 

        path = os.path.join(os.getcwd(),'userdata')
        
        if not os.path.exists(path):
            os.mkdir(path)
        
        path = os.path.join(path,f"{suid}.json")
        
        with open(path,"w",encoding="UTF-8") as file:
            file.write(json.dumps(pldata).decode("UTF-8"))

    except:
        await msg.edit("Failed to parse the playlist. Check log if you think its error.")
        torlog.exception("Playlist Parse failed") 


#todo
# Add the YT playlist feature here
# Add the YT channels feature here 