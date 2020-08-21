from telethon import TelegramClient,events 
from telethon.tl.types import KeyboardButtonCallback
from ..consts.ExecVarsSample import ExecVars
from ..core.getCommand import get_command
from ..core.getVars import get_val
from ..functions.Leech_Module import check_link,cancel_torrent,pause_all,resume_all,purge_all,get_status,print_files
from ..functions.tele_upload import upload_a_file,upload_handel
from .database_handle import TtkUpload
from .settings import handle_settings,handle_setting_callback
from functools import partial
from ..functions.rclone_upload import get_config
from ..functions.admin_check import is_admin
import asyncio as aio
import re,logging,time,os


torlog = logging.getLogger(__name__)

def add_handlers(bot: TelegramClient):
    #bot.add_event_handler(handle_leech_command,events.NewMessage(func=lambda e : command_process(e,get_command("LEECH")),chats=ExecVars.ALD_USR))
    bot.add_event_handler(
        handle_leech_command,
        events.NewMessage(pattern=command_process(get_command("LEECH")),
        chats=ExecVars.ALD_USR)
    )
    
    bot.add_event_handler(
        handle_purge_command,
        events.NewMessage(pattern=command_process(get_command("PURGE")),
        chats=ExecVars.ALD_USR)
    )
    
    bot.add_event_handler(
        handle_pauseall_command,
        events.NewMessage(pattern=command_process(get_command("PAUSEALL")),
        chats=ExecVars.ALD_USR)
    )
    
    bot.add_event_handler(
        handle_resumeall_command,
        events.NewMessage(pattern=command_process(get_command("RESUMEALL")),
        chats=ExecVars.ALD_USR)
    )

    bot.add_event_handler(
        handle_status_command,
        events.NewMessage(pattern=command_process(get_command("STATUS")),
        chats=ExecVars.ALD_USR)
    )

    bot.add_event_handler(
        handle_settings_command,
        events.NewMessage(pattern=command_process(get_command("SETTINGS")),
        chats=ExecVars.ALD_USR)
    )

    bot.add_event_handler(
        handle_exec_message_f,
        events.NewMessage(pattern=command_process(get_command("EXEC")),
        chats=ExecVars.ALD_USR)
    )
    
    
    bot.add_event_handler(
        handle_test_command,
        events.NewMessage(pattern="/test",
        chats=ExecVars.ALD_USR)
    )

    

    #*********** Callback Handlers *********** 
    
    bot.add_event_handler(
        callback_handler,
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

#*********** Handlers Below ***********

async def handle_leech_command(e):
    # get the callback in convs
    async def get_c_data(e,sid,li):
        if e.sender_id == sid:
            li[0] = e.data.decode("UTF-8")
            await e.answer("Got the selection")
            return True
        else:
            await e.answer("Dont touch someone eles leech.",alert=True)
            return False

    # get the value in list [only way ]
    choice = [""]
    #create a partial for lambda
    get_c_par = partial(get_c_data,li=choice)

    if not e.is_reply:
        await e.reply("Reply to a link or magnet")
    else:
        rclone = False
        # convo init
        if await get_config() is not None:
            async with e.client.conversation(e.chat_id) as conv:
                buts = [[KeyboardButtonCallback("To Drive",data="leechselect drive")],[KeyboardButtonCallback("To Telegram",data="leechselect tg")]]
                conf_mes = await conv.send_message("<b>Choose where to upload your files:- </b>",parse_mode="html",buttons=buts,reply_to=e.id)
                
                try:
                    await conv.wait_event(
                        events.CallbackQuery(
                            pattern="leechselect",
                            func=lambda ne: get_c_par(ne,e.sender_id)
                        ),
                        timeout=60
                    )
                except aio.exceptions.TimeoutError:
                    torlog.error("Choice for the user got timeout fallback to default")
                    defleech = get_val("DEFAULT_TIMEOUT")
                    
                    if defleech == "leech":
                        rclone = False
                    elif defleech == "rclone":
                        rclone = True
                    else:
                        # just in case something goes wrong
                        rclone = False
                else:
                    if choice[0].find("drive") != -1:
                        rclone = True
                    else:
                        rclone = False
                finally:
                    await conf_mes.delete()

        if rclone:
            if get_val("RCLONE_ENABLED"):
                await check_link(e,rclone)
            else:
                await e.reply("<b>DRIVE IS DISABLED BY THE ADMIN</b>",parse_mode="html")
        else:
            if get_val("LEECH_ENABLED"):
                await check_link(e,rclone)
            else:
                await e.reply("<b>TG LEECH IS DISABLED BY THE ADMIN</b>",parse_mode="html")

            #path = await check_link(e)
            #if path is not None:
            #    pass

#add admin checks here - done
async def handle_purge_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await purge_all(e)
    else:
        await e.delete()

async def handle_pauseall_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await pause_all(e)
    else:
        await e.delete()

async def handle_resumeall_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await resume_all(e)
    else:
        await e.delete()

async def handle_settings_command(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_settings(e)
    else:
        await e.delete()

async def handle_status_command(e):
    cmds = e.text.split(" ")
    if len(cmds) > 1:
        if cmds[1] == "all":
            await get_status(e,True)
        else:
            await get_status(e)
    else:
        await get_status(e)
        

async def handle_test_command(e):
    #print(await is_admin(e.client,e.sender_id,e.chat_id))
    db = TtkUpload()
    await upload_a_file("/mnt/d/oc/The.Dude.In.Me.2019.720p.HDRip.850MB.Ganool.mkv",e,False,db)
    pass

async def handle_settings_cb(e):
    if await is_admin(e.client,e.sender_id,e.chat_id):
        await handle_setting_callback(e)
    else:
        await e.answer("⚠️ WARN ⚠️ Dont Touch Admin Settings.",alert=True)

async def handle_upcancel_cb(e):
    db = TtkUpload()

    data = e.data.decode("UTF-8")
    print("Data is ",data)
    data = data.split(" ")

    if str(e.sender_id) == data[3]:
        db.cancel_download(data[1],data[2])
        await e.answer("CANCLED UPLOAD")
    else:
        await e.answer("Cant Cancel others upload 😡",alert=True)


async def callback_handler(e):
    
    mes = await e.get_message()
    mes = await mes.get_reply_message()
    
    torlog.info(f"Here the sender _id is {e.sender_id}")
    torlog.info("here is the allower users list {} {}".format(get_val("ALD_USR"),type(get_val("ALD_USR"))))

    if mes.sender_id == e.sender_id:
        hashid = str(e.data).split(" ")[1]
        hashid = hashid.strip("'")
        torlog.info(f"Hashid :- {hashid}")

        await cancel_torrent(hashid)
        await e.answer("The torrent has been cancled ;)",alert=True)
    elif e.sender_id in get_val("ALD_USR"):
        hashid = str(e.data).split(" ")[1]
        hashid = hashid.strip("'")
        
        torlog.info(f"Hashid :- {hashid}")
        
        await cancel_torrent(hashid)
        await e.answer("The torrent has been cancled in ADMIN MODE XD ;)",alert=True)
    else:
        await e.answer("You can cancel only your torrents ;)", alert=True)


async def handle_exec_message_f(e):
    message = e
    client = e.client
    if await is_admin(client, message.sender_id, message.chat_id):
        PROCESS_RUN_TIME = 100
        cmd = message.text.split(" ", maxsplit=1)[1]

        reply_to_id = message.id
        if message.is_reply:
            reply_to_id = message.reply_to_msg_id

        start_time = time.time() + PROCESS_RUN_TIME
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
                chat_id=message.chat_id,
                document="exec.text",
                caption=cmd,
                reply_to=reply_to_id
            )
            os.remove("exec.text")
            await message.delete()
        else:
            await message.reply(OUTPUT)


def command_process(command):
    return re.compile(command,re.IGNORECASE)