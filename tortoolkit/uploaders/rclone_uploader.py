# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from configparser import ConfigParser
from posix import listdir
from sys import path
from ..core.base_task import BaseTask
from ..core.getVars import get_val
from ..database.dbhandler import TorToolkitDB, TtkUpload
import os
import logging
from telethon.tl.types import KeyboardButtonUrl, KeyboardButtonCallback
import subprocess
import asyncio
import json
import time
import re
from urllib import parse
from ..utils.size import calculate_size
from requests.utils import requote_uri
from ..status.rclone_status import RcloneStatus
from ..status.status_manager import StatusManager
from ..database.dbhandler import TorToolkitDB
from ..utils.misc_utils import clear_stuff


torlog = logging.getLogger(__name__)

class RcloneUploader(BaseTask):
    class RcloneStatus:
        def __init__(self, uploaded, speed, eta, prg) -> None:
            self.uploaded = uploaded
            self.speed = speed
            self.eta = eta
            self.prg = prg

    def __init__(self, path, user_msg, dest_drive=None):
        super().__init__()
        self._path = path
        self._user_msg = user_msg
        self._rclone_pr = None
        self._current_update = None
        self._dest_drive = dest_drive

    async def execute(self):
        path = self._path
        upload_db = TtkUpload()
        if self._dest_drive is None:
            dest_drive = get_val("DEF_RCLONE_DRIVE")
        else:
            dest_drive = self._dest_drive
        
        if get_val("ENABLE_SA_SUPPORT_FOR_GDRIVE") and dest_drive == "sas_acc":
            print("in sas")
            conf_path = await self.gen_sa_rc_file()
        else:
            print("not in sas")
            conf_path = await self.get_config()
        
        if conf_path is None:
            torlog.info("The rclone config file was not found.")
            self._is_errored = True
            self._error_reason = "The rclone config file was not found."
            return False
        
        conf = ConfigParser()
        conf.read(conf_path)
        is_gdrive = False
        is_odrive = False
        is_general = False
        general_drive_name = ""

        for i in conf.sections():
            if dest_drive == str(i):
                if conf[i]["type"] == "drive":
                    is_gdrive = True
                    dest_base = get_val("GDRIVE_BASE_DIR")
                    torlog.info("Google Drive Upload Detected.")
                elif conf[i]["type"] == "onedrive":
                    is_odrive = True
                    dest_base = get_val("ONEDRIVE_BASE_DIR")
                    torlog.info("OneDrive Upload Detected.")
                else:
                    is_general = True
                    general_drive_name = conf[i]["type"]
                    dest_base = get_val("RCLONE_BASE_DIR")
                    torlog.info(f"{general_drive_name} Upload Detected.")
                break
        
        
        
        ul_size = calculate_size(path)
        # this function will need a driver for him :o

        if not os.path.exists(path):
            torlog.info(f"Returning none cuz the path {path} not found")
            self._is_errored = True
            self._error_reason = f"Returning none cuz the path {path} not found"
            return False

        TtkUpload().register_upload(self._user_msg.chat_id, self._user_msg.id)
        iterator = 0

        while True:
            iterator += 1
            if iterator > 100:
                # Fail safe condition
                self._is_errored = True
                self._error_reason = "Canceled Rclone Upload"
                return False
            
            if os.path.isdir(path):
                # handle dirs
                new_dest_base = os.path.join(dest_base,os.path.basename(path))
                # buffer size needs more testing though #todo
                if get_val("RSTUFF"):
                    rclone_copy_cmd = [get_val("RSTUFF"),'copy',f'--config={conf_path}',str(path),f'{dest_drive}:{new_dest_base}','-f','- *.!qB','--buffer-size=1M','-P']
                else:
                    rclone_copy_cmd = ['rclone','copy',f'--config={conf_path}',str(path),f'{dest_drive}:{new_dest_base}','-f','- *.!qB','--buffer-size=1M','-P']

                # spawn a process # attempt 1 # test 2
                rclone_pr = subprocess.Popen(
                    rclone_copy_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self._rclone_pr = rclone_pr
                rcres = await self.rclone_process_update()

                is_rate_limit = False
                blank = 0

                if get_val("ENABLE_SA_SUPPORT_FOR_GDRIVE") and is_gdrive:
                    while True:
                        data = rclone_pr.stderr.readline().decode()
                        data = data.strip()
                        if data == "":
                            blank += 1
                            if blank == 5:
                                self._is_completed = True
                                self._is_done = True
                                break
                        else:
                            mat = re.findall(".*User.*Rate.*(Limit|Quota).*Exceeded.*", data, re.IGNORECASE)
                            if mat is not None:
                                if len(mat) > 0:
                                    is_rate_limit = True
                                    torlog.info("Current account limit reached now changing the SA account.")
                                    await self.gen_sa_rc_file(change=True)
                                    break
                
                if rcres is False and not is_rate_limit:
                    self._is_errored = True
                    self._error_reason = "Canceled Rclone Upload"
                    rclone_pr.kill()
                    return False
                    

                torlog.info("Upload complete")
                
                if is_gdrive:
                    gid = await self.get_glink(dest_drive,dest_base,os.path.basename(path),conf_path)
                    torlog.info(f"Upload folder id :- {gid}")
                    
                    folder_link = f"https://drive.google.com/folderview?id={gid[0]}"

                    
                    gd_index = get_val("GD_INDEX_URL")
                    index_link = None

                    if gd_index:
                        index_link = "{}/{}/".format(gd_index.strip("/"), gid[1])
                        index_link = requote_uri(index_link)
                        torlog.info("index link "+str(index_link))
                    
                    #transfer[0] += ul_size
                    self._error_reason = "Uploaded Size:- {}\nUPLOADED FOLDER :-<code>{}</code>\nTo Google Drive.".format(ul_size, os.path.basename(path))
                
                elif is_odrive:
                    if ".sharepoint.com/" in get_val("ONEDRIVE_BASE_FOLDER_URL"):
                        folder_link = get_val("ONEDRIVE_BASE_FOLDER_URL") +  parse.quote("/"+os.path.basename(path))
                    else:
                        gid = await self.get_glink(dest_drive,dest_base,os.path.basename(path),conf_path)
                        ids = gid[1].split("#")
                        folder_link = "https://onedrive.live.com/?cid={}&id={}".format(ids[0], ids[1])
                    od_index = get_val("ONEDRIVE_INDEX_URL")
                    index_link = None

                    if od_index:
                        index_link = "{}/{}/".format(od_index.strip("/"), parse.quote(os.path.basename(path)))
                        index_link = requote_uri(index_link)
                        torlog.info("index link "+str(index_link))
                    self._error_reason = "Uploaded Size:- {}\nUPLOADED FOLDER :-<code>{}</code>\nTo OneDrive.".format(ul_size, os.path.basename(path))
                elif is_general:
                    folder_link = "http://localhost"
                    index_link = None

                    self._error_reason = "Uploaded Size:- {}\nUPLOADED FOLDER :-<code>{}</code>\nTo {}.".format(ul_size, os.path.basename(path), general_drive_name)
                
                TtkUpload().deregister_upload(self._user_msg.chat_id, self._user_msg.id)
                if not is_rate_limit:
                    return folder_link, index_link

            else:
                new_dest_base = dest_base
                # buffer size needs more testing though #todo
                if get_val("RSTUFF"):
                    rclone_copy_cmd = [get_val("RSTUFF"),'copy',f'--config={conf_path}',str(path),f'{dest_drive}:{new_dest_base}','-f','- *.!qB','--buffer-size=1M','-P']
                else:
                    rclone_copy_cmd = ['rclone','copy',f'--config={conf_path}',str(path),f'{dest_drive}:{new_dest_base}','-f','- *.!qB','--buffer-size=1M','-P']

                # spawn a process # attempt 1 # test 2
                rclone_pr = subprocess.Popen(
                    rclone_copy_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self._rclone_pr = rclone_pr
                rcres = await self.rclone_process_update()
                
                # Check for errors
                is_rate_limit = False
                blank = 0
                if get_val("ENABLE_SA_SUPPORT_FOR_GDRIVE") and is_gdrive:
                    while True:
                        data = rclone_pr.stderr.readline().decode()
                        data = data.strip()
                        if data == "":
                            blank += 1
                            if blank == 5:
                                self._is_completed = True
                                self._is_done = True
                                break
                        else:
                            mat = re.findall(".*User.*Rate.*(Limit|Quota).*Exceeded.*", data, re.IGNORECASE)
                            if mat is not None:
                                if len(mat) > 0:
                                    is_rate_limit = True
                                    torlog.info("Current account limit reached now changing the SA account.")
                                    await self.gen_sa_rc_file(change=True)
                                    break


                if rcres is False and not is_rate_limit:
                    self._is_errored = True
                    self._error_reason = "Canceled Rclone Upload"
                    rclone_pr.kill()
                    return False

                torlog.info("Upload complete")
                if is_gdrive:
                    gid = await self.get_glink(dest_drive,dest_base,os.path.basename(path),conf_path,False)
                    torlog.info(f"Upload folder id :- {gid}")

                    file_link = f"https://drive.google.com/file/d/{gid[0]}/view"
                    gd_index = get_val("GD_INDEX_URL")
                    index_link = None

                    if gd_index:
                        index_link = "{}/{}".format(gd_index.strip("/"), gid[1])
                        index_link = requote_uri(index_link)
                        torlog.info("index link "+str(index_link))
                        

                    
                    #transfer[0] += ul_size
                    self._error_reason = "Uploaded Size:- {}\nUPLOADED FILE :-<code>{}</code>\nTo Google Drive.".format(ul_size, os.path.basename(path))

                elif is_odrive:
                    base_url = get_val("ONEDRIVE_BASE_FOLDER_URL")
                    if ".sharepoint.com/" in base_url:
                        file_link = base_url +  parse.quote("/"+os.path.basename(path))
                        file_link = "{}&parent={}".format(file_link, base_url.split("?id=")[-1])

                    else:
                        gid = await self.get_glink(dest_drive,dest_base,os.path.basename(path),conf_path)
                        ids = gid[1].split("#")
                        file_link = "https://onedrive.live.com/?cid={}&id={}".format(ids[0], ids[1])

                    od_index = get_val("ONEDRIVE_INDEX_URL")
                    index_link = None

                    if od_index:
                        index_link = "{}/{}".format(od_index.strip("/"), parse.quote(os.path.basename(path)))
                        index_link = requote_uri(index_link)
                        torlog.info("index link "+str(index_link))
                    
                    self._error_reason = "Uploaded Size:- {}\nUPLOADED FILE :-<code>{}</code>\nTo OneDrive.".format(ul_size, os.path.basename(path))
                elif is_general:
                    file_link = "http://localhost"
                    index_link = None

                    self._error_reason = "Uploaded Size:- {}\nUPLOADED FILE :-<code>{}</code>\nTo {}.".format(ul_size, os.path.basename(path), general_drive_name)

                TtkUpload().deregister_upload(self._user_msg.chat_id, self._user_msg.id) # deregister the upload here
                if not is_rate_limit:
                    return file_link, index_link

    async def gen_sa_rc_file(self, change=False):
        sas_number = get_val("SA_ACCOUNT_NUMBER")
        sa_td_id = get_val("SA_TD_ID")
        sa_folder_id = get_val("SA_FOLDER_ID")

        if sa_td_id != "":
            content = "[sas_acc]\n" \
                      "type = drive\n" \
                      "scope = drive\n" \
                      "team_drive = {}\n".format(sa_td_id)
        elif sa_folder_id != "":
            content = "[sas_acc]\n" \
                      "type = drive\n" \
                      "scope = drive\n" \
                      "root_folder_id = {}\n".format(sa_folder_id)
        else:
            raise Exception("SA Enabled but not configured correctly as no sa teamdrive id or folder is provided.")
        
        sa_folder = get_val("SA_ACCOUNTS_FOLDER")
        if os.path.exists(sa_folder) and os.path.isdir(sa_folder):
            total_sas = len(os.listdir(sa_folder))
            if change:
                sas_number = (sas_number+1) % total_sas
                TorToolkitDB().set_variable("SA_ACCOUNT_NUMBER", sas_number)

            content += f"service_account_file = {sa_folder}/{sas_number}.json\n"
            with open("sasrc.conf","w") as rcfile:
                rcfile.write(content)
            torlog.info(f"Using the SAS with number {sas_number}")
            return "sasrc.conf"
        else:
            raise Exception("SA Accounts folder path not found or incorrect.")
        


    async def rclone_process_update(self):
        blank=0
        sleeps = False
        start = time.time()
        process = self._rclone_pr
        edit_time = get_val("EDIT_SLEEP_SECS")

        while True:
            data = process.stdout.readline().decode()
            data = data.strip()
            mat = re.findall("Transferred:.*ETA.*",data)
            
            if mat is not None:
                if len(mat) > 0:
                    sleeps = True
                    if time.time() - start > edit_time:
                        start = time.time()
                        nstr = mat[0].replace("Transferred:","")
                        nstr = nstr.strip()
                        nstr = nstr.split(",")
                        prg = nstr[1].strip("% ")
                        self._current_update = self.RcloneStatus(nstr[0], nstr[2], nstr[3],prg)
                        
            if data == "":
                blank += 1
                if blank == 20:
                    self._is_completed = True
                    self._is_done = True
                    break
            else:
                blank = 0

            if sleeps:
                if TtkUpload().get_cancel_status(self._user_msg.chat_id, self._user_msg.id):
                    return False
                
                sleeps=False
                await asyncio.sleep(5)
                process.stdout.flush()
    
    async def get_glink(self, drive_name,drive_base,ent_name,conf_path,isdir=True):
        print("Ent - ",ent_name)
        ent_name = re.escape(ent_name)
        filter_path = os.path.join(os.getcwd(),str(time.time()).replace(".","")+".txt")
        with open(filter_path,"w",encoding="UTF-8") as file:
            file.write(f"+ {ent_name}\n")
            file.write(f"- *")

        if isdir:
            if get_val("RSTUFF"):
                get_id_cmd = [get_val("RSTUFF"), "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only", "-f", f"+ {ent_name}/", "-f", "- *"]
            else:
                get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only", "-f", f"+ {ent_name}/", "-f", "- *"]
            #get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only", f"--filter-from={filter_path}"]
        else:
            if get_val("RSTUFF"):
                get_id_cmd = [get_val("RSTUFF"), "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--files-only", "-f", f"+ {ent_name}", "-f", "- *"]
            else:
                get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--files-only", "-f", f"+ {ent_name}", "-f", "- *"]
            #get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--files-only", f"--filter-from={filter_path}"]


        # piping only stdout
        process = await asyncio.create_subprocess_exec(
            *get_id_cmd,
            stdout=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()
        stdout = stdout.decode().strip()
        
        if os.path.exists(filter_path):
            os.remove(filter_path)
        
        try:
            data = json.loads(stdout)
            id = data[0]["ID"]
            name = data[0]["Name"]
            return (id, name)
        except Exception:
            torlog.exception("Error Occured while getting id ::- {}".format(stdout))

    async def get_config(self):
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

    def cancel(self, is_admin=False):
        self._is_canceled = True
        if is_admin:
            self._canceled_by = self.ADMIN
        else: 
            self._canceled_by = self.USER
    
    async def get_update(self):
        return self._current_update

    def get_error_reason(self):
        return self._error_reason

class RcloneController:
    def __init__(self, path, user_msg, previous_task_msg = None, dest_drive = None) -> None:
        self._path = path
        self._user_msg = user_msg
        self._previous_task_msg = previous_task_msg
        self._update_msg = None
        self._dest_drive = dest_drive

    async def execute(self):
        if self._previous_task_msg is not None:
            self._update_msg = await self._previous_task_msg.reply("Starting the rclone upload.")
        else:
            self._update_msg = await self._user_msg.reply("Starting the rclone upload.")
        
        self._rclone_up = RcloneUploader(self._path, self._user_msg, self._dest_drive)

        status_msg = RcloneStatus(self, self._rclone_up, self._user_msg.sender_id)
        StatusManager().add_status(status_msg)
        status_msg.set_active()

        res = await self._rclone_up.execute()
        status_msg.set_inactive()
        
        clear_stuff(self._path)
        if self._rclone_up.is_errored:
            await self._update_msg.edit("Your Task was unsuccessful. {}".format(self._rclone_up.get_error_reason()), parse_mode="html")
        else:
            drive_link, index_link = res 
            # Add the logic to edit the message with the url buttons here only if the task was successful :)
            # TODO add buttons for the links
            buttons = [
                [KeyboardButtonUrl("Drive URL", drive_link)]
            ]
            if index_link is not None:
                buttons.append([KeyboardButtonUrl("Index URL", index_link)])
            
            await self._update_msg.delete()
            await self._user_msg.reply(self._rclone_up.get_error_reason(), buttons=buttons, parse_mode="html")

    async def get_update_message(self):
        return self._update_msg

    async def get_user_message(self):
        return self._user_msg
    
    async def get_downloader(self):
        return self._rclone_up