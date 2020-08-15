import os,subprocess,logging,re,time,json,traceback
from telethon.tl.types import KeyboardButtonUrl
import asyncio as aio
torlog = logging.getLogger(__name__)

# add user prompt here
async def rclone_upload(path,message,dest_drive,dest_base,edit_time):
    # this function will need a driver for him :o
    if not os.path.exists(path):
        return None
    
    msg = await message.reply("<b>Uplloading to configured drive.... will be updated soon.",parse_mode="html")

    if os.path.isdir(path):
        # handle dirs
        new_dest_base = os.path.join(dest_base,os.path.basename(path))
        rclone_copy_cmd = ['D:/rclone/rclone.exe','copy',str(path),f'{dest_drive}:{new_dest_base}','-P']

        # spawn a process # attempt 1 # test 2
        rclone_pr = subprocess.Popen(
            rclone_copy_cmd,
            stdout=subprocess.PIPE
        )
        await rclone_process_display(rclone_pr,edit_time,msg)
        torlog.info("Upload complete")
        gid = await get_glink(dest_drive,dest_base,os.path.basename(path))
        torlog.info(f"Upload folder id :- {gid}")

        folder_link = "https://drive.google.com/folderview?id={gid}"
        txtmsg = "UPLOADED FOLDER :-<code>{}</code>\nTo Drive.".format(os.path.basename(path))

        await msg.edit(txtmsg,buttons=[[KeyboardButtonUrl("Drive URL",folder_link)]])


    else:
        new_dest_base = dest_base
        rclone_copy_cmd = ['D:/rclone/rclone.exe','copy',str(path),f'{dest_drive}:{new_dest_base}','-P']

        # spawn a process # attempt 1 # test 2
        rclone_pr = subprocess.Popen(
            rclone_copy_cmd,
            stdout=subprocess.PIPE
        )
        await rclone_process_display(rclone_pr,edit_time,msg)
        torlog.info("Upload complete")
        gid = await get_glink(dest_drive,dest_base,os.path.basename(path),False)
        torlog.info(f"Upload folder id :- {gid}")

        file_link = "https://drive.google.com/file/d/{gid}/view"
        txtmsg = "UPLOADED FILE :-<code>{}</code>\nTo Drive.".format(os.path.basename(path))

        await msg.edit(txtmsg,buttons=[[KeyboardButtonUrl("Drive URL",file_link)]])


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
                    torlog.info(progress)
                    
            
        if data == "":
            blank += 1
            if blank == 20:
                break
        else:
            blank = 0

async def get_glink(drive_name,drive_base,ent_name,isdir=True):
    if isdir:
        get_id_cmd = ["D:/rclone/rclone.exe", "lsjson", f"{drive_name}:{drive_base}", "--dirs-only", "-f", f"+ {ent_name}/", "-f", "- *"]
    else:
        get_id_cmd = ["D:/rclone/rclone.exe", "lsjson", f"{drive_name}:{drive_base}", "--files-only", "-f", f"+ {ent_name}", "-f", "- *"]
    
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