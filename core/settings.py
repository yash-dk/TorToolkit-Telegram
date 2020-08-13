from telethon.tl.types import KeyboardButtonCallback
from telethon import events
import asyncio as aio
from .getVars import get_val
from .database_handle import TorToolkitDB
from functools import partial

# this file will contian all the handlers and code for settings
no = "❌"
yes = "✅"
header =  "<b>**TorToolKit**</b>\n<u>SETTINGS ADMIN MENU</u>"   
async def handle_setting_callback(e):
    db = TorToolkitDB()

    
    data = e.data.decode()
    cmd = data.split(" ")
    val = ""
    if cmd[1] == "fdocs":
        await e.answer("")
        if cmd[2] == "true":
            val = True
        else:
            val = False
        
        db.set_variable("FORCE_DOCUMENTS",val)
        await handle_settings(await e.get_message(),True,f"<b><u>Changed the value to {val} of force documents.</b></u>")
    elif cmd[1] == "compstr":
        #func tools works as expected ;);)
        await e.answer("Type the new value for Complete Progress String")
        lis = [False,None]
        cbak = partial(test_callback,lis=lis)

        
        e.client.add_event_handler(
            #lambda e: test_callback(e,lis),
            cbak,
            events.NewMessage()
        )
        while not lis[0]:
            await aio.sleep(1)
        val = lis[1]

        e.client.remove_event_handler(cbak)
        #e.client.remove_event_handler(await test_callback(e,lis))

        await handle_settings(await e.get_message(),True,f"<b><u>Received Complete String value '{val}'.</b></u>")

    

async def test_callback(e,lis):
    lis[0] = True
    lis[1] = e.text
    await e.delete()
    raise events.StopPropagation

async def handle_settings(e,edit=False,msg=""):
    
    menu = [
        #[KeyboardButtonCallback(yes+" Allow TG Files Leech123456789-","settings data".encode("UTF-8"))],
    ]
    
    await get_bool_variable("FORCE_DOCUMENTS","FORCE_DOCUMENTS",menu,"fdocs")
    await get_string_variable("COMPLETED_STR",menu,"compstr")

    if edit:
        rmess = await e.edit(header+"\nIts recommended to lock the group before setting vars.\n"+msg,parse_mode="html",buttons=menu)
    else:
        rmess = await e.reply(header+"\nIts recommended to lock the group before setting vars.\n",parse_mode="html",buttons=menu)

async def get_bool_variable(var_name,msg,menu,callback_name):
    val = get_val(var_name)
    
    if val:
        #setting the value in callback so calls will be reduced ;)
        menu.append(
            [KeyboardButtonCallback(yes+msg,f"settings {callback_name} false".encode("UTF-8"))]
        ) 
    else:
        menu.append(
            [KeyboardButtonCallback(no+msg,f"settings {callback_name} true".encode("UTF-8"))]
        ) 

async def get_string_variable(var_name,menu,callback_name):
    val = get_val(var_name)
    msg = var_name + " " + val
    menu.append(
        [KeyboardButtonCallback(msg,f"settings {callback_name}".encode("UTF-8"))]
    ) 