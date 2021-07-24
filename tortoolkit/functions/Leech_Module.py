# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio as aio
import logging
import os
import re
import shutil
import time

import aiohttp
from telethon.tl import types

from .. import transfer
from ..core.getVars import get_val
from ..core.status.status import ARTask, MegaDl
from ..core.status.upload import TGUploadTask
from ..functions.Human_Format import human_readable_bytes
from . import QBittorrentWrap, ariatools, megatools
from .dl_generator import generate_directs
from .megatools import megadl
from .rclone_upload import rclone_driver
from .tele_upload import upload_handel
from .zip7_utils import add_to_zip, extract_archive

# logging.basicConfig(level=logging.DEBUG)
logging.getLogger("telethon").setLevel(logging.WARNING)
torlog = logging.getLogger(__name__)

# this files main task is to keep the ability to switch to a new engine if needed ;)

# TODO major clean up in leech module.

# TODO implement multiple magnets from same message if needed
# this function is to ensure that only one magnet is passed at a time
def get_magnets(text):
    matches = [i for i in re.finditer("magnet:", text)]
    magnets = list()

    for i in range(len(matches)):
        if i == len(matches) - 1:
            magnets.append(text[matches[i].span()[0] :])
        elif i == 0:
            magnets.append(text[: matches[i + 1].span()[0]])
        else:
            magnets.append(text[matches[i].span()[0] : matches[i + 1].span()[0]])

    for i in range(len(magnets)):
        magnets[i] = magnets[i].strip()

    return magnets[0]


def get_entities(msg):
    urls = list()

    for i in msg.entities:
        if isinstance(i, types.MessageEntityUrl):
            o, l = i.offset, i.length
            urls.append(msg.text[o : o + l])
        elif isinstance(i, types.MessageEntityTextUrl):
            urls.append(i.url)

    if len(urls) > 0:
        return urls[0]
    else:
        return None


async def check_link(msg, rclone=False, is_zip=False, extract=False, prev_msg=None):
    # here moslty rmess = Reply message which the bot uses to update
    # omess = original message from the sender user
    omess = msg
    msg = await msg.get_reply_message()

    if extract:
        mess = f"You chose to extract the archive <a href='tg://user?id={omess.sender_id}'>ENTER PASSWORD IF ANY.</a>\n Use <code>/setpass {omess.id} password-here</code>"
        omess.client.dl_passwords[omess.id] = [str(omess.sender_id), None]
        await omess.reply(mess, parse_mode="html")

    if msg is None:
        pass

    elif msg.document is not None:
        name = None
        for i in msg.document.attributes:
            if isinstance(i, types.DocumentAttributeFilename):
                name = i.file_name

        if name is None:
            await omess.reply(
                "This is not a torrent file to leech from. Send <code>.torrent</code> file",
                parse_mode="html",
            )
        elif name.lower().endswith(".torrent"):
            rmess = await omess.reply("Downloading the torrent file.")

            # not worring about the download location now
            # TODO do something to de register the torrents
            path = await msg.download_media()
            torrent_return = await QBittorrentWrap.register_torrent(
                path, rmess, omess, file=True
            )

            dl_path, dl_task = None, None
            if not isinstance(torrent_return, bool) and torrent_return is not None:
                dl_path = torrent_return[0]
                dl_task = torrent_return[1]

                if extract:
                    newpath = await handle_ext_zip(dl_path, rmess, omess)
                    if not newpath is False:
                        dl_path = newpath
                else:
                    newpath = await handle_zips(dl_path, is_zip, rmess, not rclone)
                    if newpath is False:
                        pass
                    else:
                        dl_path = newpath

                # REMOVED HEROKU BLOCK

                if not rclone:
                    ul_size = calculate_size(dl_path)
                    ul_task = TGUploadTask(dl_task)
                    await ul_task.dl_files()
                    try:
                        rdict = await upload_handel(
                            dl_path,
                            rmess,
                            omess.from_id,
                            dict(),
                            user_msg=omess,
                            task=ul_task,
                        )
                    except:
                        rdict = dict()
                        torlog.exception("Exception in torrent file")

                    await ul_task.set_inactive()
                    await print_files(
                        omess, rdict, dl_task.hash, path=dl_path, size=ul_size
                    )
                    torlog.info("Here are the fiels uploaded {}".format(rdict))
                    await QBittorrentWrap.delete_this(dl_task.hash)
                else:
                    res = await rclone_driver(dl_path, rmess, omess, dl_task)
                    if res is None:
                        await msg.reply(
                            "<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",
                            parse_mode="html",
                        )
                    await QBittorrentWrap.delete_this(dl_task.hash)

            else:
                await errored_message(omess, rmess)

            await clear_stuff(path)
            await clear_stuff(dl_path)
            return dl_path
        else:
            await omess.reply(
                "This is not a torrent file to leech from. Send <code>.torrent</code> file",
                parse_mode="html",
            )

    elif msg.raw_text is not None:
        if msg.raw_text.lower().startswith("magnet:"):
            rmess = await omess.reply("Scanning....")

            mgt = get_magnets(msg.raw_text.strip())
            torrent_return = await QBittorrentWrap.register_torrent(
                mgt, rmess, omess, True
            )

            dl_path, dl_task = None, None
            if not isinstance(torrent_return, bool) and torrent_return is not None:
                dl_path = torrent_return[0]
                dl_task = torrent_return[1]

                if extract:
                    newpath = await handle_ext_zip(dl_path, rmess, omess)
                    if not newpath is False:
                        dl_path = newpath
                else:
                    newpath = await handle_zips(dl_path, is_zip, rmess, not rclone)
                    if newpath is False:
                        pass
                    else:
                        dl_path = newpath

                # REMOVED  HEROKU BLOCK

                if not rclone:
                    # TODO add exception update for tg upload everywhere
                    ul_size = calculate_size(dl_path)

                    ul_task = TGUploadTask(dl_task)
                    await ul_task.dl_files()

                    try:
                        rdict = await upload_handel(
                            dl_path,
                            rmess,
                            omess.from_id,
                            dict(),
                            user_msg=omess,
                            task=ul_task,
                        )
                    except:
                        rdict = dict()
                        torlog.exception("Exception in magnet")

                    await ul_task.set_inactive()
                    await print_files(
                        omess, rdict, dl_task.hash, path=dl_path, size=ul_size
                    )

                    torlog.info("Here are the files to be uploaded {}".format(rdict))
                    await QBittorrentWrap.delete_this(dl_task.hash)

                else:
                    res = await rclone_driver(dl_path, rmess, omess, dl_task)
                    if res is None:
                        await msg.reply(
                            "<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",
                            parse_mode="html",
                        )
                    await QBittorrentWrap.delete_this(dl_task.hash)
            else:
                await errored_message(omess, rmess)

            await clear_stuff(dl_path)

        elif msg.raw_text.lower().endswith(".torrent"):
            rmess = await omess.reply("Downloading the torrent file.")

            # TODO do something to de register the torrents - done
            path = ""
            async with aiohttp.ClientSession() as sess:
                async with sess.get(msg.raw_text) as resp:
                    if resp.status == 200:
                        path = str(time.time()).replace(".", "") + ".torrent"
                        with open(path, "wb") as fi:
                            fi.write(await resp.read())
                    else:
                        await rmess.edit(
                            "Error got HTTP response code:- " + str(resp.status)
                        )
                        return

            torrent_return = await QBittorrentWrap.register_torrent(
                path, rmess, omess, file=True
            )
            dl_path, dl_task = None, None
            if not isinstance(torrent_return, bool) and torrent_return is not None:
                dl_path = torrent_return[0]
                dl_task = torrent_return[1]

                if extract:
                    newpath = await handle_ext_zip(dl_path, rmess, omess)
                    if not newpath is False:
                        dl_path = newpath
                else:
                    newpath = await handle_zips(dl_path, is_zip, rmess, not rclone)
                    if newpath is False:
                        pass
                    else:
                        dl_path = newpath

                # REMOVED  HEROKU BLOCK

                if not rclone:
                    ul_size = calculate_size(dl_path)
                    ul_task = TGUploadTask(dl_task)
                    await ul_task.dl_files()

                    try:
                        rdict = await upload_handel(
                            dl_path,
                            rmess,
                            omess.from_id,
                            dict(),
                            user_msg=omess,
                            task=ul_task,
                        )
                    except:
                        rdict = dict()
                        torlog.exception("Exception in torrent link")

                    await ul_task.set_inactive()
                    await print_files(
                        omess, rdict, dl_task.hash, path=dl_path, size=ul_size
                    )

                    torlog.info("Here are the fiels uploaded {}".format(rdict))
                    await QBittorrentWrap.delete_this(dl_task.hash)
                else:
                    res = await rclone_driver(dl_path, rmess, omess, dl_task)
                    if res is None:
                        await msg.reply(
                            "<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",
                            parse_mode="html",
                        )
                    await QBittorrentWrap.delete_this(dl_task.hash)
            else:
                await errored_message(omess, rmess)

            await clear_stuff(path)
            await clear_stuff(dl_path)
            return dl_path

        else:
            msg.raw_text
            url = msg.raw_text

            rmsg = await omess.reply("**Processing the link...**")

            path = None
            re_name = None

            if "mega.nz" in url:
                torlog.info("Megadl Downloading:\n{}".format(url))
                dl_task = await megadl(url, rmsg, omess)
                errstr = await dl_task.get_error()

                if errstr is not None and errstr != "":
                    stat = False
                else:
                    stat = True
            else:
                torlog.info("The aria2 Downloading:\n{}".format(url))
                await aio.sleep(1)

                url = await generate_directs(url)
                if url is not None:
                    if "**ERROR:" in url:
                        await rmsg.edit(url)
                        await aio.sleep(2)
                        await errored_message(omess, rmsg)
                        return
                    else:
                        await rmsg.edit(f"**Found direct:** `{url}`")
                        await aio.sleep(2)

                try:
                    if " " in omess.raw_text:
                        cmd = omess.raw_text.split(" ", 1)[-1]
                        if len(cmd) > 0:
                            re_name = cmd
                        else:
                            torlog.info(
                                f"This is not a valid name for renaming:= {omess.raw_text}"
                            )
                except:
                    torlog.exception("Wronged in rename detect")

                # weird stuff had to refetch message
                rmsg = await omess.client.get_messages(ids=rmsg.id, entity=rmsg.chat_id)

                if url is None:
                    stat, dl_task = await ariatools.aria_dl(
                        msg.raw_text, "", rmsg, omess
                    )
                else:
                    stat, dl_task = await ariatools.aria_dl(url, "", rmsg, omess)

            if isinstance(dl_task, (ARTask, MegaDl)) and stat:
                path = await dl_task.get_path()
                if re_name:
                    try:
                        rename_path = os.path.join(os.path.dirname(path), re_name)
                        os.rename(path, rename_path)
                        path = rename_path
                    except:
                        torlog.warning("Wrong in renaming the file.")

                if extract:
                    newpath = await handle_ext_zip(path, rmsg, omess)
                    if not newpath is False:
                        path = newpath
                else:
                    newpath = await handle_zips(path, is_zip, rmsg, not rclone)
                    if newpath is False:
                        pass
                    else:
                        path = newpath

                ul_size = calculate_size(path)
                transfer[1] += ul_size  # for aria2 downloads

                if not rclone:
                    ul_task = TGUploadTask(dl_task)
                    await ul_task.dl_files()

                    try:
                        rdict = await upload_handel(
                            path,
                            rmsg,
                            omess.from_id,
                            dict(),
                            user_msg=omess,
                            task=ul_task,
                        )
                    except:
                        rdict = dict()
                        torlog.exception("Exception in Direct links.")

                    await ul_task.set_inactive()
                    await print_files(omess, rdict, path=path, size=ul_size)
                    torlog.info("Here are the files to be uploaded {}".format(rdict))
                else:
                    res = await rclone_driver(path, rmsg, omess, dl_task)
                    if res is None:
                        await msg.reply(
                            "<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",
                            parse_mode="html",
                        )
            elif stat is False:
                reason = await dl_task.get_error()
                await rmsg.edit("Failed to download this file.\n" + str(reason))
                await errored_message(omess, rmsg)

            await clear_stuff(path)
    return None


async def pause_all(msg):
    await QBittorrentWrap.pause_all(msg)


async def resume_all(msg):
    await QBittorrentWrap.resume_all(msg)


async def purge_all(msg):
    await QBittorrentWrap.delete_all(msg)


async def get_status(msg, all=False):
    smsg = await QBittorrentWrap.get_status(msg, all)
    if len(smsg) > 3600:
        chunks, chunk_size = len(smsg), len(smsg) // 4
        msgs = [smsg[i : i + chunk_size] for i in range(0, chunks, chunk_size)]

        for j in msgs:
            await msg.reply(j, parse_mode="html")
            await aio.sleep(1)
    else:
        await msg.reply(smsg, parse_mode="html")


async def handle_zips(path, is_zip, rmess, split=True):
    # refetch rmess
    rmess = await rmess.client.get_messages(rmess.chat_id, ids=rmess.id)
    if is_zip:
        try:
            await rmess.edit(
                rmess.text + "\nStarting to Zip the contents. Please wait."
            )
            zip_path = await add_to_zip(path, get_val("TG_UP_LIMIT"), split)

            if zip_path is None:
                await rmess.edit(rmess.text + "\nZip failed. Falback to normal.")
                return False

            if os.path.isdir(path):
                shutil.rmtree(path)
            if os.path.isfile(path):
                os.remove(path)
            await rmess.edit(rmess.text + "\n\nZipping done. Now uploading.")
            await clear_stuff(path)
            return zip_path
        except:
            await rmess.edit(rmess.text + "\nZip failed. Falback to normal.")
            return False
    else:
        return path


async def handle_ext_zip(path, rmess, omess):
    # refetch rmess
    rmess = await rmess.client.get_messages(rmess.chat_id, ids=rmess.id)
    password = rmess.client.dl_passwords.get(omess.id)
    if password is not None:
        password = password[1]
    start = time.time()
    await rmess.edit(
        f"{rmess.text}\nTrying to Extract the archive with password: `{password}`"
    )
    wrong_pwd = False

    while True:
        if not wrong_pwd:
            ext_path = await extract_archive(path, password=password)
        else:
            if (time.time() - start) > 1200:
                await rmess.edit(
                    f"{rmess.text}\nExtract failed as no correct password was provided uploading as it is."
                )
                return False

            temppass = rmess.client.dl_passwords.get(omess.id)
            if temppass is not None:
                temppass = temppass[1]
            if temppass == password:
                await aio.sleep(10)
                continue
            else:
                password = temppass
                wrong_pwd = False
                continue

        if isinstance(ext_path, str):
            if "Wrong Password" in ext_path:
                mess = f"<a href='tg://user?id={omess.sender_id}'>RE-ENTER PASSWORD</a>\nThe passowrd <code>{password}</code> you provided is a wrong password.You have {((time.time()-start)/60)-20} Mins to reply else un extracted zip will be uploaded.\n Use <code>/setpass {omess.id} password-here</code>"
                await omess.reply(mess, parse_mode="html")
                wrong_pwd = True
            else:
                await clear_stuff(path)
                return ext_path

        elif ext_path is False:
            return False
        elif ext_path is None:
            # None is to descibe fetal but the upload will fail
            # itself further nothing to handle here
            return False
        else:
            await clear_stuff(path)
            return ext_path


async def errored_message(e, reason):
    msg = f"<a href='tg://user?id={e.sender_id}'>Done</a>\nYour Download Failed."
    if reason is not None:
        await reason.reply(msg, parse_mode="html")
    else:
        await e.reply(msg, parse_mode="html")


async def print_files(e, files, thash=None, path=None, size=None):
    msg = f"<a href='tg://user?id={e.sender_id}'>Done</a>\n#uploads\n"

    if path is not None and size is None:
        size = calculate_size(path)
        transfer[0] += size
        size = human_readable_bytes(size)
        msg += f"Uploaded Size:- {str(size)}\n\n"
    elif size is not None:
        transfer[0] += size
        size = human_readable_bytes(size)
        msg += f"Uploaded Size:- {str(size)}\n\n"

    if len(files) == 0:
        return

    chat_id = e.chat_id
    msg_li = []
    for i in files.keys():
        link = f"https://t.me/c/{str(chat_id)[4:]}/{files[i]}"
        if len(msg + f'🚩 <a href="{link}">{i}</a>\n') > 4000:
            msg_li.append(msg)
            msg = f'🚩 <a href="{link}">{i}</a>\n'
        else:
            msg += f'🚩 <a href="{link}">{i}</a>\n'

    for i in msg_li:
        await e.reply(i, parse_mode="html")
        await aio.sleep(1)

    await e.reply(msg, parse_mode="html")

    try:
        if thash is not None:
            from .store_info_hash import store_driver  # pylint: disable=import-error

            await store_driver(e, files, thash)
    except:
        pass

    if len(files) < 2:
        return

    ids = list()
    for i in files.keys():
        ids.append(files[i])

    msgs = await e.client.get_messages(e.chat_id, ids=ids)
    for i in msgs:
        index = None
        for j in range(0, len(msgs)):
            index = j
            if ids[j] == i.id:
                break
        nextt, prev = "", ""
        chat_id = str(e.chat_id)[4:]
        buttons = []
        if index == 0:
            nextt = f"https://t.me/c/{chat_id}/{ids[index+1]}"
            buttons.append(types.KeyboardButtonUrl("Next", nextt))
            nextt = f'<a href="{nextt}">Next</a>\n'
        elif index == len(msgs) - 1:
            prev = f"https://t.me/c/{chat_id}/{ids[index-1]}"
            buttons.append(types.KeyboardButtonUrl("Prev", prev))
            prev = f'<a href="{prev}">Prev</a>\n'
        else:
            nextt = f"https://t.me/c/{chat_id}/{ids[index+1]}"
            buttons.append(types.KeyboardButtonUrl("Next", nextt))
            nextt = f'<a href="{nextt}">Next</a>\n'

            prev = f"https://t.me/c/{chat_id}/{ids[index-1]}"
            buttons.append(types.KeyboardButtonUrl("Prev", prev))
            prev = f'<a href="{prev}">Prev</a>\n'

        try:
            # await i.edit("{} {} {}".format(prev,i.text,nextt),parse_mode="html")
            await i.edit(buttons=buttons)
        except:
            pass
        await aio.sleep(2)


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


async def get_transfer():
    client = await QBittorrentWrap.get_client()
    data = client.transfer_info()
    dlbytes = data["dl_info_data"] + transfer[1]
    upbytes = data["up_info_data"] + transfer[0]
    return upbytes, dlbytes


async def clear_stuff(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except:
        pass


async def cancel_torrent(hashid, is_aria=False, is_mega=False):
    if is_aria:
        await ariatools.remove_dl(hashid)
    elif is_mega:
        await megatools.remove_mega_dl(hashid)
    else:
        await QBittorrentWrap.deregister_torrent(hashid)


def get_size_fl(start_path="."):
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size
