import asyncio,shlex,logging
import orjson as json
from telethon.hints import MessageLike
from typing import Union,List,Tuple,Dict

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

async def create_quality_menu(url: str):
    data = await get_yt_link_details(url)
    if data is None:
        return None
    else:
        unique_formats = dict()
        for i in data.get("formats"):
            c_format = i.get("format_note")
            if not c_format in unique_formats:
                unique_formats[c_format] = [i.get("filesize"),i.get("filesize")]
            else:
                if unique_formats[c_format][0] > i.get("filesize"):
                    unique_formats[c_format][0] = i.get("filesize")
                else:
                    unique_formats[c_format][1] = i.get("filesize")


        print(unique_formats)
        
        
        



if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(create_quality_menu(""))
