import asyncio
import logging
import os
import pathlib
import time
from subprocess import Popen

from megasdkrestclient import MegaSdkRestClient, constants

from ..core.getVars import get_val
from ..core.status.status import MegaDl

torlog = logging.getLogger(__name__)


async def init_mega_client(holder=[], return_pr=False):
    if len(holder) == 0:
        MEGA_API = get_val("MEGA_API")
        MEGA_UNAME = get_val("MEGA_UNAME")
        MEGA_PASS = get_val("MEGA_PASS")

        if MEGA_API is None:
            return None

        pr = Popen(["megasdkrest", "--apikey", MEGA_API, "--port", "8200"])
        await asyncio.sleep(5)
        mega_client = MegaSdkRestClient("http://localhost:8200")

        anon = False
        if MEGA_UNAME is None:
            anon = True
            torlog.warn("Mega Username not specified")

        if MEGA_PASS is None:
            anon = True
            torlog.warn("Mega Password not specified")

        if anon:
            torlog.info("Mega running in Anon mode.")

        else:
            torlog.info("Mega running in Logged in mode.")

            try:
                mega_client.login(MEGA_UNAME, MEGA_PASS)
            except:
                torlog.error("Mega login failed.")
                torlog.info("Started in anon mode.")
        holder.append(mega_client)
        holder.append(pr)

    if return_pr:
        return holder[1]
    else:
        return holder[0]


async def megadl(link, update_msg, user_msg):
    mega_client = await init_mega_client()

    path = os.path.join(os.getcwd(), "Downloads", str(time.time()).replace(".", ""))
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    dl_add_info = mega_client.addDl(link, path)

    dl_info = mega_client.getDownloadInfo(dl_add_info["gid"])

    dl_task = MegaDl(dl_add_info, dl_info, update_msg, mega_client)
    await dl_task.set_original_mess(user_msg)

    while True:
        dl_info = mega_client.getDownloadInfo(dl_add_info["gid"])
        if dl_info["state"] not in [
            constants.State.TYPE_STATE_CANCELED,
            constants.State.TYPE_STATE_FAILED,
        ]:
            if dl_info["state"] == constants.State.TYPE_STATE_COMPLETED:
                await dl_task.set_done()
                await update_msg.edit("**Download Complete**.")
                await asyncio.sleep(2)
                return dl_task
            try:
                await dl_task.refresh_info(dl_info)
                await dl_task.update_message()
                await asyncio.sleep(get_val("EDIT_SLEEP_SECS"))
            except Exception as e:
                torlog.info(e)
        else:
            if dl_info["state"] == constants.State.TYPE_STATE_CANCELED:
                await dl_task.set_inactive("Canceled by user.")
            else:
                await dl_task.set_inactive(dl_info["error_string"])
            return dl_task


async def remove_mega_dl(gid):
    mega_client = await init_mega_client()
    mega_client.cancelDl(gid)
