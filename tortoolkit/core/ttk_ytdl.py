import asyncio,shlex,logging,time,os
import orjson as json
from telethon.hints import MessageLike
from telethon.tl.types import KeyboardButtonCallback
from typing import Union,List,Tuple,Dict,Optional
from ..functions.Human_Format import human_readable_bytes

torlog = logging.getLogger(__name__)

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

async def get_max_thumb(data: dict) -> str:
    thumbnail = data.get("thumbnails")
    
    if thumbnail is None:
        thumb_url = None
    else:
        max_w = 0
        thumb_url = None
        for i in thumbnail:
            if i.get("width") > max_w:
                thumb_url = i.get("url")
                max_w = i.get("width")
    
    return thumb_url

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

async def handle_ytdl_file_download(e: MessageLike):
    data = e.data.decode("UTF-8")
    data = data.split("|")

    if data[2] != str(e.sender_id):
        await e.answer("Not valid user, Dont touch.")
        return
    
    path = os.path.join(os.getcwd(),'userdata',data[3]+".json")
    if os.path.exists(path):
        with open(path,encoding="UTF-8") as file:
            ytdata = json.loads(file.read())
            yt_url = ytdata.get("webpage_url")
            
    else:
        await e.answer("Try again something went wrong.",alert=True)
        await e.delete()

#todo
# Add the YT playlist feature here
# Add the YT channels feature here 