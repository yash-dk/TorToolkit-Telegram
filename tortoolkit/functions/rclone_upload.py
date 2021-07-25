# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio as aio
import json
import logging
import os
import re
import subprocess
import time
import traceback

from requests.utils import requote_uri
from telethon.tl.types import KeyboardButtonCallback, KeyboardButtonUrl

from .. import transfer, upload_db, var_db
from ..core.getVars import get_val
from ..core.status.upload import RCUploadTask
from . import Human_Format

torlog = logging.getLogger(__name__)


async def rclone_driver(path, message, user_msg, dl_task):
    # this driver will need to do this
    # get the default drive
    conf_path = await get_config()
    if conf_path is None:
        torlog.info("The config file was not found")
        return None
    else:
        drive_name = get_val("DEF_RCLONE_DRIVE")
        rem_base = get_val("RCLONE_BASE_DIR")
        edtime = get_val("EDIT_SLEEP_SECS")

        ul_task = RCUploadTask(dl_task)
        try:
            return await rclone_upload(
                path,
                message,
                user_msg,
                drive_name,
                rem_base,
                edtime,
                conf_path,
                ul_task,
            )
        except:
            await ul_task.set_inactive()
            torlog.exception("Stuff gone wrong in here")
            return


# add user prompt here
async def rclone_upload(
    path, message, user_msg, dest_drive, dest_base, edit_time, conf_path, task
):
    # this function will need a driver for him :o
    if not os.path.exists(path):
        torlog.info(f"Returning none cuz the path {path} not found")
        await task.set_inactive(f"Returning none cuz the path {path} not found")
        return None
    omsg = user_msg
    await task.set_original_message(omsg)
    upload_db.register_upload(omsg.chat_id, omsg.id)
    data = "upcancel {} {} {}".format(omsg.chat_id, omsg.id, omsg.sender_id)
    buts = [KeyboardButtonCallback("Cancel upload.", data.encode("UTF-8"))]

    msg = await message.reply(
        "<b>Uploading to configured drive.... will be updated soon.",
        parse_mode="html",
        buttons=buts,
    )
    await task.set_message(msg)

    if os.path.isdir(path):
        # handle dirs
        new_dest_base = os.path.join(dest_base, os.path.basename(path))
        # buffer size needs more testing though #todo
        if get_val("RSTUFF"):
            rclone_copy_cmd = [
                get_val("RSTUFF"),
                "copy",
                f"--config={conf_path}",
                str(path),
                f"{dest_drive}:{new_dest_base}",
                "-f",
                "- *.!qB",
                "--buffer-size=1M",
                "-P",
            ]
        else:
            rclone_copy_cmd = [
                "rclone",
                "copy",
                f"--config={conf_path}",
                str(path),
                f"{dest_drive}:{new_dest_base}",
                "-f",
                "- *.!qB",
                "--buffer-size=1M",
                "-P",
            ]

        # spawn a process # attempt 1 # test 2
        rclone_pr = subprocess.Popen(rclone_copy_cmd, stdout=subprocess.PIPE)
        rcres = await rclone_process_display(
            rclone_pr, edit_time, msg, message, omsg, task
        )

        if rcres is False:
            await message.edit(message.text + "\nCanceled Rclone Upload")
            await msg.delete()
            rclone_pr.kill()
            task.cancel = True
            await task.set_inactive("Canceled Rclone Upload")
            return task

        torlog.info("Upload complete")
        gid = await get_glink(dest_drive, dest_base, os.path.basename(path), conf_path)
        torlog.info(f"Upload folder id :- {gid}")

        folder_link = f"https://drive.google.com/folderview?id={gid[0]}"

        buttons = []
        buttons.append([KeyboardButtonUrl("Drive URL", folder_link)])
        gd_index = get_val("GD_INDEX_URL")
        if gd_index:
            index_link = "{}/{}/".format(gd_index.strip("/"), gid[1])
            index_link = requote_uri(index_link)
            torlog.info("index link " + str(index_link))
            buttons.append([KeyboardButtonUrl("Index URL", index_link)])

        ul_size = calculate_size(path)
        transfer[0] += ul_size
        ul_size = Human_Format.human_readable_bytes(ul_size)
        txtmsg = "<a href='tg://user?id={}'>Done</a>\n#uploads\nUploaded Size:- {}\nUPLOADED FOLDER :-<code>{}</code>\nTo Drive.".format(
            omsg.sender_id, ul_size, os.path.basename(path)
        )

        await omsg.reply(txtmsg, buttons=buttons, parse_mode="html")
        await msg.delete()

    else:
        new_dest_base = dest_base
        # buffer size needs more testing though #todo
        if get_val("RSTUFF"):
            rclone_copy_cmd = [
                get_val("RSTUFF"),
                "copy",
                f"--config={conf_path}",
                str(path),
                f"{dest_drive}:{new_dest_base}",
                "-f",
                "- *.!qB",
                "--buffer-size=1M",
                "-P",
            ]
        else:
            rclone_copy_cmd = [
                "rclone",
                "copy",
                f"--config={conf_path}",
                str(path),
                f"{dest_drive}:{new_dest_base}",
                "-f",
                "- *.!qB",
                "--buffer-size=1M",
                "-P",
            ]

        # spawn a process # attempt 1 # test 2
        rclone_pr = subprocess.Popen(rclone_copy_cmd, stdout=subprocess.PIPE)
        rcres = await rclone_process_display(
            rclone_pr, edit_time, msg, message, omsg, task
        )

        if rcres is False:
            await message.edit(message.text + "\nCanceled Rclone Upload")
            await msg.delete()
            rclone_pr.kill()
            task.cancel = True
            await task.set_inactive("Canceled Rclone Upload")
            return task

        torlog.info("Upload complete")
        gid = await get_glink(
            dest_drive, dest_base, os.path.basename(path), conf_path, False
        )
        torlog.info(f"Upload folder id :- {gid}")

        buttons = []

        file_link = f"https://drive.google.com/file/d/{gid[0]}/view"
        buttons.append([KeyboardButtonUrl("Drive URL", file_link)])
        gd_index = get_val("GD_INDEX_URL")
        if gd_index:
            index_link = "{}/{}".format(gd_index.strip("/"), gid[1])
            index_link = requote_uri(index_link)
            torlog.info("index link " + str(index_link))
            buttons.append([KeyboardButtonUrl("Index URL", index_link)])

        ul_size = calculate_size(path)
        transfer[0] += ul_size
        ul_size = Human_Format.human_readable_bytes(ul_size)
        txtmsg = "<a href='tg://user?id={}'>Done</a>\n#uploads\nUploaded Size:- {}\nUPLOADED FILE :-<code>{}</code>\nTo Drive.".format(
            omsg.sender_id, ul_size, os.path.basename(path)
        )

        await omsg.reply(txtmsg, buttons=buttons, parse_mode="html")
        await msg.delete()

    upload_db.deregister_upload(message.chat_id, message.id)
    await task.set_inactive()
    return task


async def rclone_process_display(process, edit_time, msg, omessage, cancelmsg, task):
    blank = 0
    sleeps = False
    start = time.time()
    while True:

        data = process.stdout.readline().decode()
        data = data.strip()
        mat = re.findall("Transferred:.*ETA.*", data)

        if mat is not None:
            if len(mat) > 0:
                sleeps = True
                if time.time() - start > edit_time:
                    start = time.time()

                    await task.refresh_info(data)
                    await task.update_message()

        if data == "":
            blank += 1
            if blank == 20:
                break
        else:
            blank = 0

        if sleeps:
            if upload_db.get_cancel_status(cancelmsg.chat_id, cancelmsg.id):
                return False

            sleeps = False
            await aio.sleep(2)
            process.stdout.flush()


async def get_glink(drive_name, drive_base, ent_name, conf_path, isdir=True):
    print("Ent - ", ent_name)
    ent_name = re.escape(ent_name)
    filter_path = os.path.join(os.getcwd(), str(time.time()).replace(".", "") + ".txt")
    with open(filter_path, "w", encoding="UTF-8") as file:
        file.write(f"+ {ent_name}\n")
        file.write(f"- *")

    if isdir:
        if get_val("RSTUFF"):
            get_id_cmd = [
                get_val("RSTUFF"),
                "lsjson",
                f"--config={conf_path}",
                f"{drive_name}:{drive_base}",
                "--dirs-only",
                "-f",
                f"+ {ent_name}/",
                "-f",
                "- *",
            ]
        else:
            get_id_cmd = [
                "rclone",
                "lsjson",
                f"--config={conf_path}",
                f"{drive_name}:{drive_base}",
                "--dirs-only",
                "-f",
                f"+ {ent_name}/",
                "-f",
                "- *",
            ]
        # get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--dirs-only", f"--filter-from={filter_path}"]
    else:
        if get_val("RSTUFF"):
            get_id_cmd = [
                get_val("RSTUFF"),
                "lsjson",
                f"--config={conf_path}",
                f"{drive_name}:{drive_base}",
                "--files-only",
                "-f",
                f"+ {ent_name}",
                "-f",
                "- *",
            ]
        else:
            get_id_cmd = [
                "rclone",
                "lsjson",
                f"--config={conf_path}",
                f"{drive_name}:{drive_base}",
                "--files-only",
                "-f",
                f"+ {ent_name}",
                "-f",
                "- *",
            ]
        # get_id_cmd = ["rclone", "lsjson", f'--config={conf_path}', f"{drive_name}:{drive_base}", "--files-only", f"--filter-from={filter_path}"]

    # piping only stdout
    process = await aio.create_subprocess_exec(*get_id_cmd, stdout=aio.subprocess.PIPE)

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
        torlog.error(
            "Error Occured while getting id ::- {} {}".format(
                traceback.format_exc(), stdout
            )
        )


async def get_config():
    # this car requires to access the blob

    config = get_val("RCLONE_CONFIG")
    if config is not None:
        if isinstance(config, str):
            if os.path.exists(config):
                return config

    db = var_db
    _, blob = db.get_variable("RCLONE_CONFIG")

    if blob is not None:
        fpath = os.path.join(os.getcwd(), "rclone-config.conf")
        with open(fpath, "wb") as fi:
            fi.write(blob)
        return fpath

    return None


def calculate_size(path):
    if path is not None:
        try:
            if os.path.isdir(path):
                return get_size_fl(path)
            else:
                return os.path.getsize(path)
        except:
            torlog.warning("Size Calculation Failed.")
            return 0
    else:
        return 0


def get_size_fl(start_path="."):
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size


# probably hotfix for rclone ban
