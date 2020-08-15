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
import asyncio as aio
import re,logging


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
        if get_config() is not None:
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

        
        await check_link(e,rclone)
            #path = await check_link(e)
            #if path is not None:
            #    pass

#add admin checks here
async def handle_purge_command(e):
    await purge_all(e)

async def handle_pauseall_command(e):
    await pause_all(e)
    
async def handle_resumeall_command(e):
    await resume_all(e)

async def handle_settings_command(e):
    await handle_settings(e)

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
    testmsg = await e.reply("Test Files are downloaded ;)")
    rdict = await upload_handel("/mnt/d/GitMajors/TorToolkit/test2/test.mp3",testmsg,e.sender_id,dict())
    await print_files(e,rdict)

async def handle_settings_cb(e):
    await handle_setting_callback(e)

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

def command_process(command):
    return re.compile(command,re.IGNORECASE)