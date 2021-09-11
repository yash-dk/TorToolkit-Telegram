# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio as aio
import logging
import os
import time
import traceback
import aiohttp
from datetime import datetime
from functools import partial
from random import randint

import qbittorrentapi as qba
from telethon import events
from telethon.errors.rpcerrorlist import FloodWaitError, MessageNotModifiedError
from telethon.tl.types import KeyboardButtonCallback, KeyboardButtonUrl

from .. import tor_db
from ..core.getVars import get_val
from ..core.status.status import QBTask
from . import Hash_Fetch
from .Human_Format import human_readable_bytes, human_readable_timedelta

# logging.basicConfig(level=logging.DEBUG)
torlog = logging.getLogger(__name__)
aloop = aio.get_event_loop()
logging.getLogger("qbittorrentapi").setLevel(logging.ERROR)
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)


async def get_client(
    host=None, port=None, uname=None, passw=None, retry=2
) -> qba.TorrentsAPIMixIn:
    """Creats and returns a client to communicate with qBittorrent server. Max Retries 2"""
    # getting the conn
    host = host if host is not None else "localhost"
    port = port if port is not None else "8090"
    uname = uname if uname is not None else "admin"
    passw = passw if passw is not None else "adminadmin"
    torlog.info(
        f"Trying to login in qBittorrent using creds {host} {port} {uname} {passw}"
    )

    client = qba.Client(host=host, port=port, username=uname, password=passw)

    # try to connect to the server :)
    try:
        await aloop.run_in_executor(None, client.auth_log_in)
        torlog.info("Client connected successfully to the torrent server. 😎")
        try:
            if get_val("ADD_CUSTOM_TRACKERS"):

                url = get_val("TRACKER_SOURCE")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        tracker_data = await resp.text()
            else:
                tracker_data = ""
        except:
            tracker_data = ""

        qbt_trackers_confirmation = get_val("ADD_CUSTOM_TRACKERS")

        await aloop.run_in_executor(
            None,
            client.application.set_preferences,
            {
                "add_trackers_enabled":qbt_trackers_confirmation,
                "add_trackers":tracker_data
            },
        )
        torlog.debug(
            "Setting the cache size to 64 incomplete_files_ext:True,max_connec:3000,max_connec_per_torrent:300,async_io_threads:6"
        )
        return client
    except qba.LoginFailed as e:
        torlog.error(
            "An errot occured invalid creds detected\n{}\n{}".format(
                e, traceback.format_exc()
            )
        )
        return None
    except qba.APIConnectionError:
        if retry == 0:
            torlog.error("Tried to get the client 3 times no luck")
            return None

        torlog.info(
            "Oddly enough the qbittorrent server is not running.... Attempting to start at port {}".format(
                port
            )
        )
        cmd = f"qbittorrent-nox -d --webui-port={port} --profile=."
        cmd = cmd.split(" ")

        subpr = await aio.create_subprocess_exec(
            *cmd, stderr=aio.subprocess.PIPE, stdout=aio.subprocess.PIPE
        )
        _, _ = await subpr.communicate()
        return await get_client(host, port, uname, passw, retry=retry - 1)


async def add_torrent_magnet(magnet, message):
    """Adds a torrent by its magnet link."""
    client = await get_client()
    try:
        len(await get_torrent_info(client))

        ext_hash = Hash_Fetch.get_hash_magnet(magnet)
        ext_res = await get_torrent_info(client, ext_hash)

        if len(ext_res) > 0:
            torlog.info(f"This torrent is in list {ext_res} {magnet} {ext_hash}")
            await message.edit("This torrent is alreaded in the leech list.")
            return False
        # hot fix for the below issue
        savepath = os.path.join(
            os.getcwd(), "Downloads", str(time.time()).replace(".", "")
        )
        op = await aloop.run_in_executor(
            None, partial(client.torrents_add, magnet, save_path=savepath)
        )

        # TODO uncomment the below line and remove the above fix when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
        # op = client.torrents_add(magnet)

        # torrents_add method dosent return anything so have to work around
        if op.lower() == "ok.":
            st = datetime.now()

            ext_res = await get_torrent_info(client, ext_hash)
            if len(ext_res) > 0:
                torlog.info("Got torrent info from ext hash.")
                return ext_res[0]

            while True:
                if (datetime.now() - st).seconds >= 10:
                    torlog.warning(
                        "The provided torrent was not added and it was timed out. magnet was:- {}".format(
                            magnet
                        )
                    )
                    torlog.error(ext_hash)
                    await message.edit("The torrent was not added due to an error.")
                    return False
                # commenting in favour of wrong torrent getting returned
                # ctor_new = client.torrents_info()
                # if len(ctor_new) > ctor:
                #    # https://t.me/c/1439207386/2977 below line is for this
                #    torlog.info(ctor_new)
                #    torlog.info(magnet)
                #    return ctor_new[0]
                ext_res = await get_torrent_info(client, ext_hash)
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
        torlog.error("{}\n{}".format(e, traceback.format_exc()))
        await message.edit("Error occured check logs.")
        return False


async def add_torrent_file(path, message):
    if not os.path.exists(path):
        torlog.error(
            "The path supplied to the torrent file was invalid.\n path:-{}".format(path)
        )
        return False

    client = await get_client()
    try:
        len(await get_torrent_info(client))

        ext_hash = Hash_Fetch.get_hash_file(path)
        ext_res = await get_torrent_info(client, ext_hash)

        if len(ext_res) > 0:
            torlog.info(f"This torrent is in list {ext_res} {path} {ext_hash}")
            await message.edit("This torrent is already added in the leech list.")
            return False

        # hot fix for the below issue
        savepath = os.path.join(
            os.getcwd(), "Downloads", str(time.time()).replace(".", "")
        )

        op = await aloop.run_in_executor(
            None, partial(client.torrents_add, torrent_files=[path], save_path=savepath)
        )

        # TODO uncomment the below line and remove the above fix when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
        # op = client.torrents_add(torrent_files=[path])
        # this method dosent return anything so have to work around

        if op.lower() == "ok.":
            st = datetime.now()
            # ayehi wait karna hai
            await aio.sleep(2)

            ext_res = await get_torrent_info(client, ext_hash)
            if len(ext_res) > 0:
                torlog.info("Got torrent info from ext hash.")
                return ext_res[0]

            while True:
                if (datetime.now() - st).seconds >= 20:
                    torlog.warning(
                        "The provided torrent was not added and it was timed out. file path was:- {}".format(
                            path
                        )
                    )
                    torlog.error(ext_hash)
                    await message.edit("The torrent was not added due to an error.")
                    return False
                # ctor_new = client.torrents_info()
                # if len(ctor_new) > ctor:
                #    return ctor_new[0]
                ext_res = await get_torrent_info(client, ext_hash)
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
        torlog.error("{}\n{}".format(e, traceback.format_exc()))
        await message.edit("Error occured check logs.")
        return False


async def update_progress(
    client, message, torrent, task, except_retry=0, sleepsec=None
):
    # task = QBTask(torrent, message, client)
    if sleepsec is None:
        sleepsec = get_val("EDIT_SLEEP_SECS")
    # switch to iteration from recursion as python dosent have tailing optimization :O
    # RecursionError: maximum recursion depth exceeded
    is_meta = False
    meta_time = time.time()

    while True:
        tor_info = await get_torrent_info(client, torrent.hash)
        # update cancellation
        if len(tor_info) > 0:
            tor_info = tor_info[0]
        else:
            task.cancel = True
            await task.set_inactive()
            await message.edit(
                "Torrent canceled ```{}``` ".format(torrent.name), buttons=None
            )
            return True

        if tor_info.size > (get_val("MAX_TORRENT_SIZE") * 1024 * 1024 * 1024):
            await message.edit(
                "Torrent oversized max size is {}. Try adding again and choose less files to download.".format(
                    get_val("MAX_TORRENT_SIZE")
                ),
                buttons=None,
            )
            await delete_this(tor_info.hash)
            return True
        try:
            await task.refresh_info(tor_info)
            await task.update_message()

            if tor_info.state == "metaDL":
                is_meta = True
            else:
                meta_time = time.time()
                is_meta = False

            if is_meta and (time.time() - meta_time) > get_val("TOR_MAX_TOUT"):

                await message.edit(
                    "Torrent <code>{}</code> is DEAD. [Metadata Failed]".format(
                        tor_info.name
                    ),
                    buttons=None,
                    parse_mode="html",
                )
                torlog.error(
                    "An torrent has no seeds clearing that torrent now. Torrent:- {} - {}".format(
                        tor_info.hash, tor_info.name
                    )
                )
                await delete_this(tor_info.hash)
                await task.set_inactive(
                    "Torrent <code>{}</code> is DEAD. [Metadata Failed]".format(
                        tor_info.name
                    )
                )

                return False

            try:
                if tor_info.state == "error":

                    await message.edit(
                        "Torrent <code>{}</code> errored out.".format(tor_info.name),
                        buttons=None,
                        parse_mode="html",
                    )
                    torlog.error(
                        "An torrent has error clearing that torrent now. Torrent:- {} - {}".format(
                            tor_info.hash, tor_info.name
                        )
                    )
                    await delete_this(tor_info.hash)
                    await task.set_inactive(
                        "Torrent <code>{}</code> errored out.".format(tor_info.name)
                    )

                    return False

                # aio timeout have to switch to global something
                await aio.sleep(sleepsec)

                # stop the download when download complete
                if tor_info.state == "uploading" or tor_info.state.lower().endswith(
                    "up"
                ):
                    # this is to address the situations where the name would cahnge abdruptly
                    await aloop.run_in_executor(
                        None, partial(client.torrents_pause, tor_info.hash)
                    )

                    # TODO uncomment the below line when fixed https://github.com/qbittorrent/qBittorrent/issues/13572
                    # savepath = os.path.join(tor_info.save_path,tor_info.name)
                    # hot fix
                    try:
                        savepath = os.path.join(
                            tor_info.save_path, os.listdir(tor_info.save_path)[-1]
                        )
                    except:
                        await message.edit(
                            "Download path location failed", buttons=None
                        )
                        await task.set_inactive("Download path location failed")
                        await delete_this(tor_info.hash)
                        return None

                    await task.set_path(savepath)
                    await task.set_done()
                    await message.edit(
                        "**Download completed:** `{}`\n\n**Size:** `{}`\n\n**To path:** `{}`".format(
                            tor_info.name,
                            human_readable_bytes(tor_info.total_size),
                            tor_info.save_path,
                        ),
                        buttons=None,
                    )
                    return [savepath, task]
                else:
                    # return await update_progress(client,message,torrent)
                    pass

            except (MessageNotModifiedError, FloodWaitError) as e:
                torlog.error("{}".format(e))

        except Exception as e:
            torlog.error("{}\n\n{}\n\nn{}".format(e, traceback.format_exc(), tor_info))
            try:
                await message.edit("Error occurred {}".format(e), buttons=None)
            except:
                pass
            return False


async def pause_all(message):
    client = await get_client()
    await aloop.run_in_executor(
        None, partial(client.torrents_pause, torrent_hashes="all")
    )
    await aio.sleep(1)
    msg = ""
    tors = await aloop.run_in_executor(
        None, partial(client.torrents_info, status_filter="paused|stalled")
    )
    msg += "⏸️ Paused total <b>{}</b> torrents ⏸️\n".format(len(tors))

    for i in tors:
        if i.progress == 1:
            continue
        msg += "➡️<code>{}</code> - <b>{}%</b>\n".format(
            i.name, round(i.progress * 100, 2)
        )

    await message.reply(msg, parse_mode="html")
    await message.delete()


async def resume_all(message):
    client = await get_client()

    await aloop.run_in_executor(
        None, partial(client.torrents_resume, torrent_hashes="all")
    )

    await aio.sleep(1)
    msg = ""
    tors = await aloop.run_in_executor(
        None,
        partial(
            client.torrents_info,
            status_filter="stalled|downloading|stalled_downloading",
        ),
    )

    msg += "▶️Resumed {} torrents check the status for more...▶️".format(len(tors))

    for i in tors:
        if i.progress == 1:
            continue
        msg += "➡️<code>{}</code> - <b>{}%</b>\n".format(
            i.name, round(i.progress * 100, 2)
        )

    await message.reply(msg, parse_mode="html")
    await message.delete()


async def delete_all(message):
    client = await get_client()
    tors = await get_torrent_info(client)
    msg = "☠️ Deleted <b>{}</b> torrents.☠️".format(len(tors))
    client.torrents_delete(delete_files=True, torrent_hashes="all")

    await message.reply(msg, parse_mode="html")
    await message.delete()


async def delete_this(ext_hash):
    client = await get_client()
    await aloop.run_in_executor(
        None,
        partial(client.torrents_delete, delete_files=True, torrent_hashes=ext_hash),
    )
    return True


async def get_status(message, all=False):
    client = await get_client()
    tors = await get_torrent_info(client)
    olen = 0

    if len(tors) > 0:
        msg = ""
        for i in tors:
            if i.progress == 1 and not all:
                continue
            else:
                olen += 1
                msg += "📥 <b>{} | {}% | {}/{}({}) | {} | {} | S:{} | L:{} | {}</b>\n\n".format(
                    i.name,
                    round(i.progress * 100, 2),
                    human_readable_bytes(i.completed),
                    human_readable_bytes(i.size),
                    human_readable_bytes(i.total_size),
                    human_readable_bytes(i.dlspeed, postfix="/s"),
                    human_readable_timedelta(i.eta),
                    i.num_seeds,
                    i.num_leechs,
                    i.state,
                )
        if msg.strip() == "":
            return "No torrents running currently...."
        return msg
    else:
        msg = "No torrents running currently...."
        return msg

    if olen == 0:
        msg = "No torrents running currently...."
        return msg


def progress_bar(percentage):
    """Returns a progress bar for download"""
    # percentage is on the scale of 0-1
    comp = get_val("COMPLETED_STR")
    ncomp = get_val("REMAINING_STR")
    pr = ""

    for i in range(1, 11):
        if i <= int(percentage * 10):
            pr += comp
        else:
            pr += ncomp
    return pr


async def deregister_torrent(hashid):
    client = await get_client()
    await aloop.run_in_executor(
        None, partial(client.torrents_delete, torrent_hashes=hashid, delete_files=True)
    )


async def register_torrent(entity, message, user_msg=None, magnet=False, file=False):
    client = await get_client()

    # refresh message
    message = await message.client.get_messages(message.chat_id, ids=message.id)
    if user_msg is None:
        omess = await message.get_reply_message()
    else:
        omess = user_msg

    if magnet:
        torlog.info(f"magnet :- {magnet}")
        torrent = await add_torrent_magnet(entity, message)
        if isinstance(torrent, bool):
            return False
        torlog.info(torrent)
        if torrent.progress == 1 and torrent.completion_on > 1:
            await message.edit("The provided torrent was already completly downloaded.")
            return True
        else:

            pincode = randint(1000, 9999)
            db = tor_db
            db.add_torrent(torrent.hash, pincode)

            pincodetxt = f"getpin {torrent.hash} {omess.sender_id}"

            data = "torcancel {} {}".format(torrent.hash, omess.sender_id)
            base = get_val("BASE_URL_OF_BOT")

            urll = f"{base}/tortk/files/{torrent.hash}"

            message = await message.edit(
                "Download will be automatically started after 180s of no action.",
                buttons=[
                    [
                        KeyboardButtonUrl("Choose File from link", urll),
                        KeyboardButtonCallback(
                            "Get Pincode", data=pincodetxt.encode("UTF-8")
                        ),
                    ],
                    [
                        KeyboardButtonCallback(
                            "Done Selecting Files.",
                            data=f"doneselection {omess.sender_id} {omess.id}".encode(
                                "UTF-8"
                            ),
                        )
                    ],
                ],
            )

            await get_confirm(omess)

            message = await message.edit(
                buttons=[
                    KeyboardButtonCallback("Cancel Leech", data=data.encode("UTF-8"))
                ]
            )

            db.disable_torrent(torrent.hash)

            task = QBTask(torrent, message, client)
            await task.set_original_mess(omess)
            return await update_progress(client, message, torrent, task)
    if file:
        torrent = await add_torrent_file(entity, message)
        if isinstance(torrent, bool):
            return False
        torlog.info(torrent)

        if torrent.progress == 1:
            await message.edit("The provided torrent was already downloaded.")
            return True
        else:
            pincode = randint(1000, 9999)
            db = tor_db
            db.add_torrent(torrent.hash, pincode)

            pincodetxt = f"getpin {torrent.hash} {omess.sender_id}"

            data = "torcancel {} {}".format(torrent.hash, omess.sender_id)

            base = get_val("BASE_URL_OF_BOT")

            urll = f"{base}/tortk/files/{torrent.hash}"

            message = await message.edit(
                buttons=[
                    [
                        KeyboardButtonUrl("Choose File from link", urll),
                        KeyboardButtonCallback(
                            "Get Pincode", data=pincodetxt.encode("UTF-8")
                        ),
                    ],
                    [
                        KeyboardButtonCallback(
                            "Done Selecting Files.",
                            data=f"doneselection {omess.sender_id} {omess.id}".encode(
                                "UTF-8"
                            ),
                        )
                    ],
                ]
            )

            await get_confirm(omess)

            message = await message.edit(
                buttons=[
                    KeyboardButtonCallback("Cancel Leech", data=data.encode("UTF-8"))
                ]
            )

            db.disable_torrent(torrent.hash)

            task = QBTask(torrent, message, client)
            await task.set_original_mess(omess)
            return await update_progress(client, message, torrent, task)


async def get_confirm(e):
    # abstract for getting the confirm in a context

    lis = [False, None, e.id]
    cbak = partial(get_confirm_callback, lis=lis)

    e.client.add_event_handler(
        # lambda e: test_callback(e,lis),
        cbak,
        events.CallbackQuery(pattern="doneselection"),
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= 180:
            break
        await aio.sleep(1)

    val = lis[1]

    e.client.remove_event_handler(cbak)

    return val


async def get_confirm_callback(e, lis):
    # handle the confirm callback
    data = e.data.decode("UTF-8")
    data = data.split(" ")
    o_sender = data[1]
    msgid = data[2]

    if o_sender != str(e.sender_id):
        await e.answer("Dont Touch it.......")
        return
    if str(lis[2]) != msgid:
        return
    await e.answer("Starting the download with the selected files.")
    lis[0] = True
    raise events.StopPropagation()


# quick async functions


async def get_torrent_info(client, ehash=None):

    if ehash is None:
        return await aloop.run_in_executor(None, client.torrents_info)
    else:
        return await aloop.run_in_executor(
            None, partial(client.torrents_info, torrent_hashes=ehash)
        )
