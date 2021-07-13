# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

from ..uploaders.telegram_uploader import TelegramUploader
from telethon import TelegramClient,events 
from telethon import __version__ as telever
from pyrogram import __version__ as pyrover
from telethon.tl.types import KeyboardButtonCallback
from ..core.getCommand import get_command
from ..core.getVars import get_val
from ..utils.speedtest import get_speed
from ..utils import human_format
from ..downloaders.qbittorrent_downloader import QbittorrentDownloader
from .settings import handle_settings,handle_setting_callback
from .user_settings import handle_user_settings, handle_user_setting_callback
from functools import partial
from ..utils.admin_check import is_admin
from .. import upload_db, var_db, tor_db, user_db, uptime
import asyncio as aio
import re,logging,time,os,psutil,shutil
from tortoolkit import __version__
from ..downloaders.ytdl_downloader import handle_ytdl_command,handle_ytdl_callbacks,handle_ytdl_playlist
torlog = logging.getLogger(__name__)
from .status.status import Status
from .status.menu import create_status_menu, create_status_user_menu
import signal
from PIL import Image
from .task_sequencer import TaskSequence
from ..status.status_manager import StatusManager

def add_handlers(bot: TelegramClient):
    #bot.add_event_handler(handle_leech_command,events.NewMessage(func=lambda e : command_process(e,get_command("LEECH")),chats=ExecVars.ALD_USR))
    
    bot.add_event_handler(
        handle_leech_command,
        events.NewMessage(pattern=command_process(get_command("LEECH")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_purge_command,
        events.NewMessage(pattern=command_process(get_command("PURGE")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_pauseall_command,
        events.NewMessage(pattern=command_process(get_command("PAUSEALL")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_resumeall_command,
        events.NewMessage(pattern=command_process(get_command("RESUMEALL")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_status_command,
        events.NewMessage(pattern=command_process(get_command("STATUS")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_u_status_command,
        events.NewMessage(pattern=command_process(get_command("USTATUS")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_settings_command,
        events.NewMessage(pattern=command_process(get_command("SETTINGS")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_exec_message_f,
        events.NewMessage(pattern=command_process(get_command("EXEC")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        upload_document_f,
        events.NewMessage(pattern=command_process(get_command("UPLOAD")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_ytdl_command,
        events.NewMessage(pattern=command_process(get_command("YTDL")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_ytdl_playlist,
        events.NewMessage(pattern=command_process(get_command("PYTDL")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        about_me,
        events.NewMessage(pattern=command_process(get_command("ABOUT")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        get_logs_f,
        events.NewMessage(pattern=command_process(get_command("GETLOGS")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        handle_test_command,
        events.NewMessage(pattern="/test",
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_server_command,
        events.NewMessage(pattern=command_process(get_command("SERVER")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        set_password_zip,
        events.NewMessage(pattern=command_process("/setpass"),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        handle_user_settings_,
        events.NewMessage(pattern=command_process(get_command("USERSETTINGS")))
    )

    bot.add_event_handler(
        start_handler,
        events.NewMessage(pattern=command_process(get_command("START")))
    )

    bot.add_event_handler(
        clear_thumb_cmd,
        events.NewMessage(pattern=command_process(get_command("CLRTHUMB")),
        chats=get_val("ALD_USR"))
    )

    bot.add_event_handler(
        set_thumb_cmd,
        events.NewMessage(pattern=command_process(get_command("SETTHUMB")),
        chats=get_val("ALD_USR"))
    )
    
    bot.add_event_handler(
        speed_handler,
        events.NewMessage(pattern=command_process(get_command("SPEEDTEST")),
        chats=get_val("ALD_USR"))
    )


    signal.signal(signal.SIGINT, partial(term_handler,client=bot))
    signal.signal(signal.SIGTERM, partial(term_handler,client=bot))
    bot.loop.run_until_complete(booted(bot))

    #*********** Callback Handlers *********** 
    
    bot.add_event_handler(
        callback_handler_canc,
        events.CallbackQuery(pattern="torcancel")
    )

    bot.add_event_handler(
        handle_settings_cb,
        events.CallbackQuery(pattern="setting")
    )

    bot.add_event_handler(
        handle_upcancel_cb,
        events.CallbackQuery(pattern="upcancel")
    )

    bot.add_event_handler(
        handle_pincode_cb,
        events.CallbackQuery(pattern="getpin")
    )

    bot.add_event_handler(
        handle_ytdl_callbacks,
        events.CallbackQuery(pattern="ytdlsmenu")
    )

    bot.add_event_handler(
        handle_ytdl_callbacks,
        events.CallbackQuery(pattern="ytdlmmenu")
    )
    
    bot.add_event_handler(
        handle_ytdl_file_download,
        events.CallbackQuery(pattern="ytdldfile")
    )
    
    bot.add_event_handler(
        handle_ytdl_playlist_down,
        events.CallbackQuery(pattern="ytdlplaylist")
    )

    bot.add_event_handler(
        handle_user_setting_callback,
        events.CallbackQuery(pattern="usetting")
    )
    bot.add_event_handler(
        handle_server_command,
        events.CallbackQuery(pattern="fullserver")
    )
#*********** Handlers Below ***********

async def handle_leech_command(e):
    if not e.is_reply:
        await e.reply("Reply to a link or magnet")
    else:
        sequencer = TaskSequence(e, await e.get_reply_message(), TaskSequence.LEECH)
        res = await sequencer.execute()
        torlog.info("Sequencer out"+ str(res))
        

#       ###### Qbittorrent Related ######

async def handle_purge_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        msg = await QbittorrentDownloader(None, None).delete_all()
        await e.reply(msg)
        await e.delete()
    else:
        await e.delete()

async def handle_pauseall_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        msg = await QbittorrentDownloader(None, None).pause_all()
        await e.reply(msg)
        await e.delete()
    else:
        await e.delete()

async def handle_resumeall_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        msg = await QbittorrentDownloader(None, None).resume_all()
        await e.reply(msg)
        await e.delete()
    else:
        await e.delete()

#       ###### Qbittorrent Related End ######

async def handle_ytdl_file_download(e):
    message = await e.get_message()
    taskseq = TaskSequence(await message.get_reply_message(),e,TaskSequence.YTDL)
    await taskseq.execute()

async def handle_ytdl_playlist_down(e):
    message = await e.get_message()
    taskseq = TaskSequence(await message.get_reply_message(),e,TaskSequence.PYTDL)
    await taskseq.execute()

async def handle_settings_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_settings(e)
    else:
        await e.delete()

async def handle_status_command(e):
    # TODO work on status command
    await StatusManager().generate_central_update(e)
    return
    cmds = e.text.split(" ")
    if len(cmds) > 1:
        if cmds[1] == "all":
            await get_status(e,True)
        else:
            await get_status(e)
    else:
        await create_status_menu(e)

async def handle_u_status_command(e):
    await create_status_user_menu(e)


async def speed_handler(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await get_speed(e)

    
async def handle_test_command(e):
    pass
    


async def handle_settings_cb(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_setting_callback(e)
    else:
        await e.answer("⚠️ WARN ⚠️ Dont Touch Admin Settings.",alert=True)


async def handle_upcancel_cb(e):
    db = upload_db

    data = e.data.decode("UTF-8")
    torlog.info("Data is {}".format(data))
    data = data.split(" ")

    if str(e.sender_id) == data[3]:
        db.cancel_download(data[1],data[2])
        await e.answer("Upload has been canceled ;)",alert=True)
    elif e.sender_id in get_val("ALD_USR"):
        db.cancel_download(data[1],data[2])
        await e.answer("UPLOAD CANCELED IN ADMIN MODE XD ;)",alert=True)
    else:
        await e.answer("Can't Cancel others upload 😡",alert=True)

async def callback_handler_canc(e):
    # TODO the msg can be deleted
    #mes = await e.get_message()
    #mes = await mes.get_reply_message()
    

    torlog.debug(f"Here the sender _id is {e.sender_id}")
    torlog.debug("here is the allower users list {} {}".format(get_val("ALD_USR"),type(get_val("ALD_USR"))))

    data = e.data.decode("utf-8").split(" ")
    torlog.debug("data is {}".format(data))
    
    is_aria = False
    is_mega = False

    if data[1] == "aria2":
        is_aria = True
        data.remove("aria2")
    
    if data[1] == "megadl":
        is_mega = True
        data.remove("megadl")
    

    if data[2] == str(e.sender_id):
        hashid = data[1]
        hashid = hashid.strip("'")
        torlog.info(f"Hashid :- {hashid}")
        #affected to aria2 too, soo
        await TaskSequence(None, None, None).cancel_task(hashid, is_aria, is_mega)
    
        await e.answer("Leech has been canceled ;)",alert=True)
    elif e.sender_id in get_val("ALD_USR"):
        hashid = data[1]
        hashid = hashid.strip("'")
        
        torlog.info(f"Hashid :- {hashid}")
        
        await TaskSequence(None, None, None).cancel_task(hashid, is_aria, is_mega)
        await e.answer("Leech has been canceled in ADMIN MODE XD ;)",alert=True)
    
    else:
        await e.answer("Can't Cancel others leech 😡", alert=True)


async def handle_exec_message_f(e):
    if get_val("REST11"):
        return
    message = e
    client = e.client
    if await is_admin(client, message.sender_id, message.chat_id, force_owner=True):
        PROCESS_RUN_TIME = 100
        cmd = message.text.split(" ", maxsplit=1)[1]

        reply_to_id = message.id
        if message.is_reply:
            reply_to_id = message.reply_to_msg_id

        process = await aio.create_subprocess_shell(
            cmd,
            stdout=aio.subprocess.PIPE,
            stderr=aio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        e = stderr.decode()
        if not e:
            e = "No Error"
        o = stdout.decode()
        if not o:
            o = "No Output"
        else:
            _o = o.split("\n")
            o = "`\n".join(_o)
        OUTPUT = f"**QUERY:**\n__Command:__\n`{cmd}` \n__PID:__\n`{process.pid}`\n\n**stderr:** \n`{e}`\n**Output:**\n{o}"

        if len(OUTPUT) > 3900:
            with open("exec.text", "w+", encoding="utf8") as out_file:
                out_file.write(str(OUTPUT))
            await client.send_file(
                entity=message.chat_id,
                file="exec.text",
                caption=cmd,
                reply_to=reply_to_id
            )
            os.remove("exec.text")
            await message.delete()
        else:
            await message.reply(OUTPUT)
    else:
        await message.reply("Only for owner")

async def handle_pincode_cb(e):
    data = e.data.decode("UTF-8")
    data = data.split(" ")
    
    if str(e.sender_id) == data[2]:
        db = tor_db
        passw = db.get_password(data[1])
        if isinstance(passw,bool):
            await e.answer("torrent expired download has been started now.")
        else:
            await e.answer(f"Your Pincode is {passw}",alert=True)

        
    else:
        await e.answer("It's not your torrent.",alert=True)

async def upload_document_f(message):
    imsegd = await message.reply(
        "processing ..."
    )
    imsegd = await message.client.get_messages(message.chat_id,ids=imsegd.id)
    if await is_admin(message.client, message.sender_id, message.chat_id, force_owner=True):
        if " " in message.text:
            recvd_command, local_file_name = message.text.split(" ", 1)
            try:
                tgup = TelegramUploader(local_file_name, imsegd)
                await tgup.execute()
            except Exception as e:
                await imsegd.edit(e)
            #torlog.info(recvd_response)
    else:
        await message.reply("Only for owner")
    await imsegd.delete()

async def get_logs_f(e):
    if await is_admin(e.client,e.sender_id,e.chat_id, force_owner=True):
        await e.client.send_file(
            entity=e.chat_id,
            file="torlog.txt",
            caption="torlog.txt",
            reply_to=e.message.id
        )
    else:
        await e.delete()

async def set_password_zip(message):
    #/setpass message_id password
    data = message.raw_text.split(" ")
    passdata = message.client.dl_passwords.get(int(data[1]))
    if passdata is None:
        await message.reply(f"No entry found for this job id {data[1]}")
    else:
        print(message.sender_id)
        print(passdata[0])
        if str(message.sender_id) == passdata[0]:
            message.client.dl_passwords[int(data[1])][1] = data[2]
            await message.reply(f"Password updated successfully.")
        else:
            await message.reply(f"Cannot update the password this is not your download.")

async def start_handler(event):
    msg = "Hello This is TorToolkit an instance of <a href='https://github.com/yash-dk/TorToolkit-Telegram'>This Repo</a>. Try the repo for yourself and dont forget to put a STAR and fork."
    await event.reply(msg, parse_mode="html")

def progress_bar(percentage):
    """Returns a progress bar for download
    """
    #percentage is on the scale of 0-1
    comp = get_val("COMPLETED_STR")
    ncomp = get_val("REMAINING_STR")
    pr = ""

    if isinstance(percentage, str):
        return "NaN"

    try:
        percentage=int(percentage)
    except:
        percentage = 0

    for i in range(1,11):
        if i <= int(percentage/10):
            pr += comp
        else:
            pr += ncomp
    return pr

async def handle_server_command(message):
    print(type(message))
    if isinstance(message, events.CallbackQuery.Event):
        callbk = True
    else:
        callbk = False

    try:
        # Memory
        mem = psutil.virtual_memory()
        memavailable = human_format.human_readable_bytes(mem.available)
        memtotal = human_format.human_readable_bytes(mem.total)
        mempercent = mem.percent
        memfree = human_format.human_readable_bytes(mem.free)
    except:
        memavailable = "N/A"
        memtotal = "N/A"
        mempercent = "N/A"
        memfree = "N/A"

    try:
        # Frequencies
        cpufreq = psutil.cpu_freq()
        freqcurrent = cpufreq.current
        freqmax = cpufreq.max
    except:
        freqcurrent = "N/A"
        freqmax = "N/A"

    try:
        # Cores
        cores = psutil.cpu_count(logical=False)
        lcores = psutil.cpu_count()
    except:
        cores = "N/A"
        lcores = "N/A"

    try:
        cpupercent = psutil.cpu_percent()
    except:
        cpupercent = "N/A"
    
    try:
        # Storage
        usage = shutil.disk_usage("/")
        totaldsk = human_format.human_readable_bytes(usage.total)
        useddsk = human_format.human_readable_bytes(usage.used)
        freedsk = human_format.human_readable_bytes(usage.free)
    except:
        totaldsk = "N/A"
        useddsk = "N/A"
        freedsk = "N/A"


    try:
        upb, dlb = 0,0
        dlb = human_format.human_readable_bytes(dlb)
        upb = human_format.human_readable_bytes(upb)
    except:
        dlb = "N/A"
        upb = "N/A"

    diff = time.time() - uptime
    diff = human_format.human_readable_timedelta(diff)

    if callbk:
        msg = (
            f"<b>BOT UPTIME:-</b> {diff}\n\n"
            "<b>CPU STATS:-</b>\n"
            f"Cores: {cores} Logical: {lcores}\n"
            f"CPU Frequency: {freqcurrent}  Mhz Max: {freqmax}\n"
            f"CPU Utilization: {cpupercent}%\n"
            "\n"
            "<b>STORAGE STATS:-</b>\n"
            f"Total: {totaldsk}\n"
            f"Used: {useddsk}\n"
            f"Free: {freedsk}\n"
            "\n"
            "<b>MEMORY STATS:-</b>\n"
            f"Available: {memavailable}\n"
            f"Total: {memtotal}\n"
            f"Usage: {mempercent}%\n"
            f"Free: {memfree}\n"
            "\n"
            "<b>TRANSFER INFO:</b>\n"
            f"Download: {dlb}\n"
            f"Upload: {upb}\n"
        )
        await message.edit(msg, parse_mode="html", buttons=None)
    else:
        try:
            storage_percent = round((usage.used/usage.total)*100,2)
        except:
            storage_percent = 0

        
        msg = (
            f"<b>BOT UPTIME:-</b> {diff}\n\n"
            f"CPU Utilization: {progress_bar(cpupercent)} - {cpupercent}%\n\n"
            f"Storage used:- {progress_bar(storage_percent)} - {storage_percent}%\n"
            f"Total: {totaldsk} Free: {freedsk}\n\n"
            f"Memory used:- {progress_bar(mempercent)} - {mempercent}%\n"
            f"Total: {memtotal} Free: {memfree}\n\n"
            f"Transfer Download:- {dlb}\n"
            f"Transfer Upload:- {upb}\n"
        )
        await message.reply(msg, parse_mode="html", buttons=[[KeyboardButtonCallback("Get detailed stats.","fullserver")]])


async def about_me(message):
    db = var_db
    _, val1 = db.get_variable("RCLONE_CONFIG")
    if val1 is None:
        rclone_cfg = "No Rclone Config is loaded."
    else:
        rclone_cfg = "Rclone Config is loaded"

    val1  = get_val("RCLONE_ENABLED")
    if val1 is not None:
        if val1:
            rclone = "Rclone enabled by admin."
        else:
            rclone = "Rclone disabled by admin."
    else:
        rclone = "N/A"

    val1  = get_val("LEECH_ENABLED")
    if val1 is not None:
        if val1:
            leen = "Leech command enabled by admin."
        else:
            leen = "Leech command disabled by admin."
    else:
        leen = "N/A"


    diff = time.time() - uptime
    diff = human_format.human_readable_timedelta(diff)

    msg = (
        "<b>Name</b>: <code>TorToolkit</code>\n"
        f"<b>Version</b>: <code>{__version__}</code>\n"
        f"<b>Telethon Version</b>: {telever}\n"
        f"<b>Pyrogram Version</b>: {pyrover}\n"
        "<b>Created By</b>: @yaknight\n\n"
        "<u>Currents Configs:-</u>\n\n"
        f"<b>Bot Uptime:-</b> {diff}\n"
        "<b>Torrent Download Engine:-</b> <code>qBittorrent [4.3.0 fix active]</code> \n"
        "<b>Direct Link Download Engine:-</b> <code>aria2</code> \n"
        "<b>Upload Engine:-</b> <code>RCLONE</code> \n"
        "<b>Youtube Download Engine:-</b> <code>youtube-dl</code>\n"
        f"<b>Rclone config:- </b> <code>{rclone_cfg}</code>\n"
        f"<b>Leech:- </b> <code>{leen}</code>\n"
        f"<b>Rclone:- </b> <code>{rclone}</code>\n"
        "\n"
        f"<b>Latest {__version__} Changelog :- </b>\n"
        "1.DB Optimizations.\n"
        "2.Mongo DB and Postgres DB both are supported.\n"
        "3.Mega Enable/Disable feature.\n"
        "4.Progress for YTDL (in beta implementation).\n"
        "5.Progress for PYTDL (in beta implementation).\n"
        "6.Re written Qbit Interface.\n"
        "7.Re written Aria2 Interface.\n"
        "8.Re written Mega Interface.\n"
        "9.Re written TGUpload Interface.\n"
        "10.Re written Rclone Interface.\n"
        "11.Major project structure change.\n"
        "12.Change the web server interface.\n"
        "13.Add ability to access downloaded data on the server from web server.\n"
        "14.Major changes will prevail soon.\n"
    )

    await message.reply(msg,parse_mode="html")


async def set_thumb_cmd(e):
    thumb_msg = await e.get_reply_message()
    if thumb_msg is None:
        await e.reply("Reply to a photo or photo as a document.")
        return
    
    if thumb_msg.document is not None or thumb_msg.photo is not None:
        value = await thumb_msg.download_media()
    else:
        await e.reply("Reply to a photo or photo as a document.")
        return

    try:
        im = Image.open(value)
        im.convert("RGB").save(value,"JPEG")
        im = Image.open(value)
        im.thumbnail((320,320), Image.ANTIALIAS)
        im.save(value,"JPEG")
        with open(value,"rb") as fi:
            data = fi.read()
            user_db.set_thumbnail(data, e.sender_id)
        os.remove(value)
    except Exception:
        torlog.exception("Set Thumb")
        await e.reply("Errored in setting thumbnail.")
        return
    
    try:
        os.remove(value)
    except:pass

    user_db.set_var("DISABLE_THUMBNAIL",False, str(e.sender_id))
    await e.reply("Thumbnail set. try using /usettings to get more control. Can be used in private too.")

async def clear_thumb_cmd(e):
    user_db.set_var("DISABLE_THUMBNAIL",True, str(e.sender_id))
    await e.reply("Thumbnail disabled. Try using /usettings to get more control. Can be used in private too.")

async def handle_user_settings_(message):
    if not message.sender_id in get_val("ALD_USR"):
        if not get_val("USETTINGS_IN_PRIVATE") and message.is_private:
            return

    await handle_user_settings(message)

def term_handler(signum, frame, client):
    torlog.info("TERM RECEIVD")
    async def term_async():
        omess = None
        st = Status().Tasks
        msg = "Bot Rebooting Re Add your Tasks\n\n"
        for i in st:
            if not await i.is_active():
                continue

            omess = await i.get_original_message()
            if str(omess.chat_id).startswith("-100"):
                chat_id = str(omess.chat_id)[4:]
                chat_id = int(chat_id)
            else:
                chat_id = omess.chat_id
            
            sender = await i.get_sender_id()
            msg += f"<a href='tg://user?id={sender}'>REBOOT</a> - <a href='https://t.me/c/{chat_id}/{omess.id}'>Task</a>\n"
        
        if omess is not None:
            await omess.respond(msg, parse_mode="html")
        exit(0)

    client.loop.run_until_complete(term_async())

async def booted(client):
    chats = get_val("ALD_USR")
    for i in chats:
        try:
            await client.send_message(i, "The bot is booted and is ready to use.")
        except Exception as e:
            torlog.info(f"Not found the entity {i}")

def command_process(command):
    return re.compile(command,re.IGNORECASE)
