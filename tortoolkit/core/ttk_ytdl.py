# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio
import json
import logging
import os
import shlex
import shutil
import time
from functools import partial
from typing import Dict, List, Optional, Tuple, Union

import aiohttp
from PIL import Image
from telethon import events
from telethon.hints import MessageLike
from telethon.tl.types import KeyboardButtonCallback, KeyboardButtonUrl

from ..core.getVars import get_val
from ..functions.Human_Format import human_readable_bytes
from ..functions.rclone_upload import get_config, rclone_driver
from ..functions.tele_upload import upload_handel

torlog = logging.getLogger(__name__)

# attempt to decorate error prone areas
def skipTorExp(func):
    def wrap_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            torlog.error(e)
            return

    return wrap_func


async def cli_call(cmd: Union[str, List[str]]) -> Tuple[str, str]:
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    elif isinstance(cmd, (list, tuple)):
        pass
    else:
        return None, None

    process = await asyncio.create_subprocess_exec(
        *cmd, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()

    with open("test.txt", "w", encoding="UTF-8") as f:
        f.write(stdout)

    return stdout, stderr


async def get_yt_link_details(url: str) -> Union[Dict[str, str], None]:
    cmd = "yt-dlp --no-warnings --youtube-skip-dash-manifest --dump-json"
    cmd = shlex.split(cmd)
    if "hotstar" in url:
        cmd.append("--geo-bypass-country")
        cmd.append("IN")
    cmd.append(url)

    out, error = await cli_call(cmd)
    if error:
        torlog.error(f"Error occured:- {error} for url {url}")
    # sanitize the json
    out = out.replace("\n", ",")
    out = "[" + out + "]"
    try:
        return json.loads(out)[0], None
    except:
        torlog.exception("Error occured while parsing the json.\n")
        return None, error


async def get_max_thumb(data: dict, suid: str) -> str:
    thumbnail = data.get("thumbnail")
    thumb_path = None

    # alot of context management XD
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                thumb_path = os.path.join(os.getcwd(), "userdata")
                if not os.path.exists(thumb_path):
                    os.mkdir(thumb_path)

                thumb_path = os.path.join(thumb_path, f"{suid}.webp")
                with open(thumb_path, "wb") as ifile:
                    ifile.write(await resp.read())

        Image.open(thumb_path).convert("RGB").save(thumb_path)

        return thumb_path
    except:
        torlog.exception("Error in thumb gen")
        return None


async def create_quality_menu(
    url: str,
    message: MessageLike,
    message1: MessageLike,
    dest: str,
    jsons: Optional[str] = None,
    suid: Optional[str] = None,
):
    if jsons is None:
        data, err = await get_yt_link_details(url)
        suid = str(time.time()).replace(".", "")
    else:
        data = jsons

    # with open("test.txt","w") as f:
    #    f.write(json.dumps(data))

    if data is None:
        return None, err
    else:
        unique_formats = dict()
        for i in data.get("formats",[]):
            c_format = i.get("format_note")
            if c_format is None:
                c_format = i.get("height")
            if not c_format in unique_formats:
                if i.get("filesize") is not None:
                    unique_formats[c_format] = [i.get("filesize"), i.get("filesize")]
                else:
                    unique_formats[c_format] = [0, 0]

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
                text = f"tiny [{human_readable_bytes(unique_formats[i][0])} - {human_readable_bytes(unique_formats[i][1])}] ➡️"
                cdata = (
                    f"ytdlsmenu|{i}|{message1.sender_id}|{suid}|{dest}"  # add user id
                )
            else:
                text = f"{i} [{human_readable_bytes(unique_formats[i][0])} - {human_readable_bytes(unique_formats[i][1])}] ➡️"
                cdata = (
                    f"ytdlsmenu|{i}|{message1.sender_id}|{suid}|{dest}"  # add user id
                )
            buttons.append([KeyboardButtonCallback(text, cdata.encode("UTF-8"))])
        buttons.append(
            [
                KeyboardButtonCallback(
                    "Audios ➡️", f"ytdlsmenu|audios|{message1.sender_id}|{suid}|{dest}"
                )
            ]
        )
        await message.edit("Choose a quality/option available below.", buttons=buttons)

        if jsons is None:
            path = os.path.join(os.getcwd(), "userdata")

            if not os.path.exists(path):
                os.mkdir(path)

            path = os.path.join(path, f"{suid}.json")

            with open(path, "w", encoding="UTF-8") as file:
                file.write(json.dumps(data))

    return True, None


async def handle_ytdl_command(e: MessageLike):
    if not e.is_reply:
        await e.reply("Reply to a youtube video link.")
        return
    msg = await e.get_reply_message()

    tsp = time.time()
    buts = [[KeyboardButtonCallback("To Telegram", data=f"ytdlselect tg {tsp}")]]
    if await get_config() is not None:
        buts.append(
            [KeyboardButtonCallback("To Drive", data=f"ytdlselect drive {tsp}")]
        )

    msg1 = await e.reply(
        f"Processing the given link......\nChoose destination. Default destination will be chosen in {get_val('DEFAULT_TIMEOUT')}.",
        buttons=buts,
    )

    choice = await get_ytdl_choice(e, tsp)
    msg1 = await msg1.edit("Processing the given link.......", buttons=None)
    await asyncio.sleep(1)

    if msg.text.find("http") != -1:
        res, err = await create_quality_menu(msg.text.strip(), msg1, msg, choice)
        if res is None:
            await msg1.edit(
                f"<code>Invalid link provided.\n{err}</code>", parse_mode="html"
            )
    else:
        await e.reply("Invalid link provided.")


async def handle_ytdl_callbacks(e: MessageLike):
    # ytdlsmenu | format | sender_id | suid | dest
    data = e.data.decode("UTF-8")
    data = data.split("|")

    if data[0] == "ytdlsmenu":
        if data[2] != str(e.sender_id):
            await e.answer("Not valid user, Dont touch.")
            return

        path = os.path.join(os.getcwd(), "userdata", data[3] + ".json")
        if os.path.exists(path):
            with open(path) as file:
                ytdata = json.loads(file.read())
                buttons = list()
                if data[1] == "audios":
                    for i in ["64K", "128K", "320K"]:
                        text = f"{i} [MP3]"
                        cdata = f"ytdldfile|{i}|{e.sender_id}|{data[3]}|{data[4]}"
                        buttons.append(
                            [KeyboardButtonCallback(text, cdata.encode("UTF-8"))]
                        )
                else:
                    j = 0
                    for i in ytdata.get("formats",[]):
                        c_format = i.get("format_note")
                        format_id = i.get("format_id")
                        height = i.get("format")
                        if c_format is None:
                            c_format = str(i.get("height"))
                            format_id = f"xxother{j}"
                            height = i.get("format")
                        if not c_format == data[1]:
                            continue

                        if not height:
                            continue

                        text = f"{height} [{i.get('ext')}] [{human_readable_bytes(i.get('filesize'))}] {str(i.get('vcodec'))}"
                        cdata = (
                            f"ytdldfile|{format_id}|{e.sender_id}|{data[3]}|{data[4]}"
                        )

                        buttons.append(
                            [KeyboardButtonCallback(text, cdata.encode("UTF-8"))]
                        )
                        j += 1

                buttons.append(
                    [
                        KeyboardButtonCallback(
                            "Go Back 😒", f"ytdlmmenu|{data[2]}|{data[3]}|{data[4]}"
                        )
                    ]
                )
                await e.edit(
                    f"Files for quality {data[1]}, at the end it is the Video Codec. Mostly prefer the last one with you desired extension if you want streamable video. Try rest if you want.",
                    buttons=buttons,
                )

        else:
            await e.answer("Try again something went wrong.", alert=True)
            await e.delete()
    elif data[0] == "ytdlmmenu":
        if data[1] != str(e.sender_id):
            await e.answer("Not valid user, Dont touch.")
            return
        path = os.path.join(os.getcwd(), "userdata", data[2] + ".json")
        if os.path.exists(path):
            with open(path, encoding="UTF-8") as file:
                ytdata = json.loads(file.read())
                await create_quality_menu(
                    "", await e.get_message(), e, data[3], ytdata, data[2]
                )

        else:
            await e.answer("Try again something went wrong.", alert=True)
            await e.delete()


async def handle_ytdl_file_download(e: MessageLike):
    # ytdldfile | format_id | sender_id | suid | dest

    data = e.data.decode("UTF-8")
    data = data.split("|")

    if data[2] != str(e.sender_id):
        await e.answer("Not valid user, Dont touch.")
        return
    else:
        await e.answer("Crunching Data.....")

    await e.edit(buttons=None)

    is_audio = False

    path = os.path.join(os.getcwd(), "userdata", data[3] + ".json")
    if os.path.exists(path):
        with open(path, encoding="UTF-8") as file:
            ytdata = json.loads(file.read())
            yt_url = ytdata.get("webpage_url")
            thumb_path = await get_max_thumb(ytdata, data[3])

            op_dir = os.path.join(os.getcwd(), "userdata", data[3])
            if not os.path.exists(op_dir):
                os.mkdir(op_dir)
            if data[1].startswith("xxother"):
                data[1] = data[1].replace("xxother", "")
                data[1] = int(data[1])
                j = 0
                for i in ytdata.get("formats",[]):
                    if j == data[1]:
                        data[1] = i.get("format_id")
                    j += 1
            else:
                for i in ytdata.get("formats",[]):
                    if i.get("format_id") == data[1]:
                        print(i)
                        if i.get("acodec") is not None:
                            if "none" not in i.get("acodec"):
                                is_audio = True

            if data[1].endswith("K"):
                cmd = f"yt-dlp -i --extract-audio --add-metadata --audio-format mp3 --audio-quality {data[1]} -o '{op_dir}/%(title)s.%(ext)s' {yt_url}"

            else:
                if is_audio:
                    cmd = f"yt-dlp --continue --embed-subs --no-warnings --hls-prefer-ffmpeg --prefer-ffmpeg -f {data[1]} -o {op_dir}/%(title)s.%(ext)s {yt_url}"
                else:
                    cmd = f"yt-dlp --continue --embed-subs --no-warnings --hls-prefer-ffmpeg --prefer-ffmpeg -f {data[1]}+bestaudio[ext=m4a]/best -o {op_dir}/%(title)s.%(ext)s {yt_url}"

            out, err = await cli_call(cmd)

            if not err:

                # TODO Fix the original thumbnail
                # rdict = await upload_handel(op_dir,await e.get_message(),e.sender_id,dict(),thumb_path=thumb_path)

                if data[4] == "tg":
                    rdict = await upload_handel(
                        op_dir, await e.get_message(), e.sender_id, dict(), user_msg=e
                    )
                    await print_files(e, rdict)
                else:
                    res = await rclone_driver(op_dir, await e.get_message(), e, None)
                    if res is None:
                        torlog.error("Error in YTDL Rclone upload.")

                shutil.rmtree(op_dir)
                os.remove(thumb_path)
                os.remove(path)
            else:
                torlog.error(err)
                omess = await e.get_message()
                omess1 = await omess.get_reply_message()
                if "HTTP Error 429" in err:
                    emsg = "HTTP Error 429: Too many requests try after a while."
                else:
                    emsg = "An error has occured trying to upload any files that are found here."
                await omess.edit(emsg)
                if omess1 is None:
                    await omess.respond(emsg)
                else:
                    await omess1.reply(emsg)

                if data[4] == "tg":
                    rdict = await upload_handel(
                        op_dir, await e.get_message(), e.sender_id, dict(), user_msg=e
                    )
                    await print_files(e, rdict)
                else:
                    res = await rclone_driver(op_dir, await e.get_message(), e, None)
                    if res is None:
                        torlog.error("Error in YTDL Rclone upload.")

                try:
                    shutil.rmtree(op_dir)
                    os.remove(thumb_path)
                    os.remove(path)
                except:
                    pass

    else:
        await e.delete()
        await e.answer("Try again something went wrong.", alert=True)
        await e.delete()


async def handle_ytdl_playlist(e: MessageLike) -> None:
    if not e.is_reply:
        await e.reply("Reply to a youtube playlist link.")
        return
    url = await e.get_reply_message()
    url = url.text.strip()
    cmd = f"yt-dlp -i --flat-playlist --dump-single-json --no-warnings {url}"

    tsp = time.time()
    buts = [[KeyboardButtonCallback("To Telegram", data=f"ytdlselect tg {tsp}")]]
    if await get_config() is not None:
        buts.append(
            [KeyboardButtonCallback("To Drive", data=f"ytdlselect drive {tsp}")]
        )

    msg = await e.reply(
        f"Processing your Youtube Playlist download request.\nChoose destination. Default destination will be chosen in {get_val('DEFAULT_TIMEOUT')}.",
        buttons=buts,
    )

    choice = await get_ytdl_choice(e, tsp)  # blocking call
    msg = await msg.edit(
        "Processing your Youtube Playlist download request.", buttons=None
    )
    await asyncio.sleep(1)

    # cancel the playlist if time exceed 5 mins
    try:
        out, err = await asyncio.wait_for(cli_call(cmd), 300)
    except asyncio.TimeoutError:
        await msg.edit(
            "Processing time exceeded... The playlist seem to long to be worked with 😢\n If the playlist is short and you think its error report back."
        )
        return

    if err:
        await msg.edit(
            f"Failed to load the playlist with the error:- <code>{err}</code>",
            parse_mode="html",
        )
        return

    try:
        pldata = json.loads(out)
        entities = pldata.get("entries")
        if len(entities) <= 0:
            await msg.edit(
                "Cannot load the videos from this playlist ensure that the playlist is not <code>'My Mix or Mix'</code>. It shuold be a public or unlisted youtube playlist."
            )
            return

        entlen = len(entities)
        keybr = list()

        # limit the max vids
        if entlen > get_val("MAX_YTPLAYLIST_SIZE"):

            await msg.edit(
                f"Playlist too large max {get_val('MAX_YTPLAYLIST_SIZE')} vids allowed as of now. This has {entlen}"
            )
            return

        # format> ytdlplaylist | quality | suid | sender_id
        suid = str(time.time()).replace(".", "")

        for i in ["144", "240", "360", "480", "720", "1080", "1440", "2160"]:
            keybr.append(
                [
                    KeyboardButtonCallback(
                        text=f"{i}p All videos",
                        data=f"ytdlplaylist|{i}|{suid}|{e.sender_id}|{choice}",
                    )
                ]
            )

        keybr.append(
            [
                KeyboardButtonCallback(
                    text=f"Best All videos",
                    data=f"ytdlplaylist|best|{suid}|{e.sender_id}|{choice}",
                )
            ]
        )

        keybr.append(
            [
                KeyboardButtonCallback(
                    text="Best all audio only. [340k]",
                    data=f"ytdlplaylist|320k|{suid}|{e.sender_id}|{choice}",
                )
            ]
        )
        keybr.append(
            [
                KeyboardButtonCallback(
                    text="Medium all audio only. [128k]",
                    data=f"ytdlplaylist|128k|{suid}|{e.sender_id}|{choice}",
                )
            ]
        )
        keybr.append(
            [
                KeyboardButtonCallback(
                    text="Worst all audio only. [64k]",
                    data=f"ytdlplaylist|64k|{suid}|{e.sender_id}|{choice}",
                )
            ]
        )

        await msg.edit(f"Found {entlen} videos in the playlist.", buttons=keybr)

        path = os.path.join(os.getcwd(), "userdata")

        if not os.path.exists(path):
            os.mkdir(path)

        path = os.path.join(path, f"{suid}.json")

        with open(path, "w", encoding="UTF-8") as file:
            file.write(json.dumps(pldata))

    except:
        await msg.edit(
            "Failed to parse the playlist. Check log if you think its error."
        )
        torlog.exception("Playlist Parse failed")


async def handle_ytdl_playlist_down(e: MessageLike) -> None:
    # ytdlplaylist | quality | suid | sender_id | choice(tg/drive)

    data = e.data.decode("UTF-8").split("|")

    if data[3] != str(e.sender_id):
        await e.answer("Not valid user, Dont touch.")
        return
    else:
        await e.answer("Crunching Data.....")

    await e.edit(buttons=None)
    path = os.path.join(os.getcwd(), "userdata", data[2] + ".json")
    if os.path.exists(path):
        await e.answer("Processing Please wait")
        opdir = os.path.join(os.getcwd(), "userdata", data[2])
        if not os.path.exists(opdir):
            os.mkdir(opdir)

        with open(path) as file:
            pldata = json.loads(file.read())
        url = pldata.get("webpage_url")

        if data[1].endswith("k"):
            audcmd = f"yt-dlp -i --extract-audio --add-metadata --audio-format mp3 --audio-quality {data[1]} -o '{opdir}/%(playlist_index)s - %(title)s.%(ext)s' {url}"
            out, err = await cli_call(audcmd)

            ofiles = len(os.listdir(opdir))

            if err and ofiles < 2:
                await e.reply(
                    f"Failed to download the audios <code>{err}</code>",
                    parse_mode="html",
                )
            else:
                if err:
                    await e.reply(
                        "Some videos from this have errored in download. Uploading which are successfull."
                    )

                if data[4] == "tg":
                    rdict = await upload_handel(
                        opdir, await e.get_message(), e.sender_id, dict(), user_msg=e
                    )
                    await print_files(e, rdict)
                else:
                    res = await rclone_driver(opdir, await e.get_message(), e, None)
                    if res is None:
                        torlog.error("Error in YTDL Rclone upload.")

        else:
            if data[1] == "best":
                vidcmd = f"yt-dlp -i --continue --embed-subs --no-warnings --prefer-ffmpeg -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best' -o '{opdir}/%(playlist_index)s - %(title)s.%(ext)s' {url}"
            else:
                vidcmd = f"yt-dlp -i --continue --embed-subs --no-warnings --prefer-ffmpeg -f 'bestvideo[ext=mp4][height<={data[1]}]+bestaudio[ext=m4a]/best' -o '{opdir}/%(playlist_index)s - %(title)s.%(ext)s' {url}"
            out, err = await cli_call(vidcmd)

            ofiles = len(os.listdir(opdir))

            if err and ofiles < 2:
                await e.reply(
                    f"Failed to download the videos <code>{err}</code>",
                    parse_mode="html",
                )
            else:
                if err:
                    await e.reply(
                        "Some videos from this have errored in download. Uploading which are successfull."
                    )

                if data[4] == "tg":
                    rdict = await upload_handel(
                        opdir, await e.get_message(), e.sender_id, dict(), user_msg=e
                    )
                    await print_files(e, rdict)
                else:
                    res = await rclone_driver(opdir, await e.get_message(), e, None)
                    if res is None:
                        torlog.error("Error in YTDL Rclone upload.")
        shutil.rmtree(opdir)
        os.remove(path)
    else:
        await e.delete()
        await e.answer("Something went wrong try again.", alert=True)
        torlog.error("the file for that suid was not found.")


async def print_files(e, files):

    msg = "#uploads\n"
    if len(files) == 0:
        return

    chat_id = e.chat_id

    for i in files.keys():
        link = f"https://t.me/c/{str(chat_id)[4:]}/{files[i]}"
        msg += f'🚩 <a href="{link}">{i}</a>\n'

    rmsg = await e.client.get_messages(e.chat_id, ids=e.message_id)
    rmsg = await rmsg.get_reply_message()
    if rmsg is None:
        # msg += "\n<a href='tg://user?id={}'>Done<a>".format(rmsg.sender_id)
        msg += "\n<a href='tg://user?id={}'>Done</a>".format(e.sender_id)
        await e.reply(msg, parse_mode="html")
    else:
        msg += "\n<a href='tg://user?id={}'>Done</a>".format(rmsg.sender_id)
        await rmsg.reply(msg, parse_mode="html")

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
            buttons.append(KeyboardButtonUrl("Next", nextt))
            nextt = f'<a href="{nextt}">Next</a>\n'
        elif index == len(msgs) - 1:
            prev = f"https://t.me/c/{chat_id}/{ids[index-1]}"
            buttons.append(KeyboardButtonUrl("Prev", prev))
            prev = f'<a href="{prev}">Prev</a>\n'
        else:
            nextt = f"https://t.me/c/{chat_id}/{ids[index+1]}"
            buttons.append(KeyboardButtonUrl("Next", nextt))
            nextt = f'<a href="{nextt}">Next</a>\n'

            prev = f"https://t.me/c/{chat_id}/{ids[index-1]}"
            buttons.append(KeyboardButtonUrl("Prev", prev))
            prev = f'<a href="{prev}">Prev</a>\n'

        try:
            # await i.edit("{} {} {}".format(prev,i.text,nextt),parse_mode="html")
            await i.edit(buttons=buttons)
        except:
            pass
        await asyncio.sleep(1)


async def get_ytdl_choice(e, timestamp):
    # abstract for getting the confirm in a context

    lis = [False, None]
    cbak = partial(
        get_leech_choice_callback, o_sender=e.sender_id, lis=lis, ts=timestamp
    )

    # REMOVED HEROKU BLOCK

    e.client.add_event_handler(
        # lambda e: test_callback(e,lis),
        cbak,
        events.CallbackQuery(pattern="ytdlselect"),
    )

    start = time.time()
    defleech = get_val("DEFAULT_TIMEOUT")

    while not lis[0]:
        if (time.time() - start) >= 60:  # TIMEOUT_SEC:

            if defleech == "leech":
                return "tg"
            elif defleech == "rclone":
                return "drive"
            else:
                # just in case something goes wrong
                return "tg"
            break
        await asyncio.sleep(1)

    val = lis[1]

    e.client.remove_event_handler(cbak)

    return val


async def get_leech_choice_callback(e, o_sender, lis, ts):
    # handle the confirm callback

    if o_sender != e.sender_id:
        return
    data = e.data.decode().split(" ")
    if data[2] != str(ts):
        return

    lis[0] = True

    lis[1] = data[1]


# todo
# Add the YT playlist feature here
# Add the YT channels feature here
