import os,subprocess,logging,re,time,json,traceback
from telethon.tl.types import KeyboardButtonUrl
import asyncio as aio
from ..core.getVars import get_val
from ..core.database_handle import TorToolkitDB

torlog = logging.getLogger(__name__)


async def rclone_driver(path,message):
    # this driver will need to do this
    # get the default drive
    conf_path = await get_config()
    if conf_path is None:
        return None
    else:
        drive_name = get_val("DEF_RCLONE_DRIVE")
        rem_base = get_val("RCLONE_BASE_DIR")
        edtime = get_val("EDIT_SLEEP_SECS")

        return await rclone_upload(path,message,drive_name,rem_base,edtime,conf_path)
    

# add user prompt here
async def rclone_upload(path,message,dest_drive,dest_base,edit_time,conf_path):
    # this function will need a driver for him :o
    if not os.path.exists(path):
        return None
    
    msg = await message.reply("<b>Uploading to configured drive.... will be updated soon.",parse_mode="html")

    if os.path.isdir(path):
        # handle dirs
        new_dest_base = os.path.join(dest_base,os.path.basename(path))
        rclone_copy_cmd = ['rclone','copy',f'--config={conf_path}',str(path),f'{dest_drive}:{new_dest_base}','-P']

        # spawn a process # attempt 1 # test 2
        rclone_pr = subprocess.Popen(
            rclone_copy_cmd,
            stdout=subprocess.PIPE
        )
        await rclone_process_display(rclone_pr,edit_time,msg)
        torlog.info("Upload complete")
        gid = await get_glink(dest_drive,dest_base,os.path.basename(path),conf_path)
        torlog.info(f"Upload folder id :- {gid}")

        folder_link = f"https://drive.google.com/folderview?id={gid}"
        txtmsg = "UPLOADED FOLDER :-<code>{}</code>\nTo Drive.".format(os.path.basename(path))

        await msg.edit(txtmsg,buttons=[[KeyboardButtonUrl("Drive URL",folder_link)]],parse_mode="html")


    else:
        new_dest_base = dest_base
        rclone_copy_cmd = ['rclone','copy',f'--config={conf_path}',str(path),f'{dest_drive}:{new_dest_base}','-P']

        # spawn a process # attempt 1 # test 2
        rclone_pr = subprocess.Popen(
            rclone_copy_cmd,
            stdout=subprocess.PIPE
        )
        await rclone_process_display(rclone_pr,edit_time,msg)
        torlog.info("Upload complete")
        gid = await get_glink(dest_drive,dest_base,os.path.basename(path),conf_path,False)
        torlog.info(f"Upload folder id :- {gid}")

        file_link = f"https://drive.google.com/file/d/{gid}/view"
        txtmsg = "UPLOADED FILE :-<code>{}</code>\nTo Drive.".format(os.path.basename(path))

        await msg.edit(txtmsg,buttons=[[KeyboardButtonUrl("Drive URL",file_link)]],parse_mode="html")
    
    return True


async def rclone_process_display(process,edit_time,msg):
    blank=0
    start = time.time()
    while True:
        
        data = process.stdout.readline().decode()
        data = data.strip()
        mat = re.findall("Transferred:.*ETA.*",data)
        
        if mat is not None:
            if len(mat) > 0:
                if time.time() - start > edit_time:
                    start = time.time()

                    nstr = mat[0].replace("Transferred:","")
                    nstr = nstr.strip()
                    nstr = nstr.split(",")
                    progress = "<b>Uploaded:- {} \nProgress:- {} \nSpeed:- {} \nETA:- {}</b>".format(nstr[0],nstr[1],nstr[2],nstr[3].replace("ETA",""))
                    await msg.edit(progress,parse_mode="html")
                    torlog.debug(progress)
                    
            
        if data == "":
            blank += 1
            if blank == 20:
                break
        else:
            blank = 0

async def get_glink(drive_name,drive_base,ent_name,conf_path,isdir=True):
    ent_name = re.escape(ent_name)
    if isdir:
        get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only", "-f", f"+ {ent_name}/", "-f", "- *"]
    else:
        get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--files-only", "-f", f"+ {ent_name}", "-f", "- *"]


    # piping only stdout
    process = await aio.create_subprocess_exec(
        *get_id_cmd,
        stdout=aio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()
    stdout = stdout.decode().strip()
    try:
        data = json.loads(stdout)
        id = data[0]["ID"]
        return id
    except Exception:
        torlog.error("Error Occured while getting id ::- {}".format(traceback.format_exc()))

async def get_config():
    # this car requires to access the blob

    config = get_val("RCLONE_CONFIG")
    if config is not None:
        if isinstance(config,str):
            if os.path.exists(config):
                return config
    
    db = TorToolkitDB()
    _, blob = db.get_variable("RCLONE_CONFIG")
    
    if blob is not None:
        fpath = os.path.join(os.getcwd(),"rclone-config.conf")
        with open(fpath,"wb") as fi:
            fi.write(blob)
        return fpath
    
    return None