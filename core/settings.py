from telethon.tl.types import KeyboardButtonCallback
from telethon import events
import asyncio as aio
from .getVars import get_val
from .database_handle import TorToolkitDB
from functools import partial
import time

TIMEOUT_SEC = 60

# this file will contian all the handlers and code for settings
# code can be more modular i think but not bothering now
# todo make the code more modular
no = "❌"
yes = "✅"
header =  "<b>**TorToolKit**</b>\n<u>ADMIN SETTINGS MENU - Beta v1</u>"   
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
        await e.answer("Type the new value for Complete Progress String. Note that only one character is expected.",alert=True)

        mmes = await e.get_message()
        val = await get_value(e)

        await general_input_manager(e,mmes,"COMPLETED_STR","str",val[0],db)
        
    
    elif cmd[1] == "remstr":
        # what will a general manager require
        # anser message, type handler, value 
        await e.answer("Type the new value for Remaining Progress String. Note that only one character is expected.",alert=True)

        mmes = await e.get_message()
        val = await get_value(e)
        
        await general_input_manager(e,mmes,"REMAINING_STR","str",val[0],db)
    
    elif cmd[1] == "tguplimit":
        # what will a general manager require
        # anser message, type handler, value 
        await e.answer("Type the new value for TELEGRAM UPLOAD LIMIT. Note that integer is expected.",alert=True)

        mmes = await e.get_message()
        val = await get_value(e)
        
        await general_input_manager(e,mmes,"TG_UP_LIMIT","int",val,db)

        


async def handle_settings(e,edit=False,msg=""):
    # this function creates the menu

    menu = [
        #[KeyboardButtonCallback(yes+" Allow TG Files Leech123456789-","settings data".encode("UTF-8"))], # for ref
    ]
    
    await get_bool_variable("FORCE_DOCUMENTS","FORCE_DOCUMENTS",menu,"fdocs")
    await get_string_variable("COMPLETED_STR",menu,"compstr")
    await get_string_variable("REMAINING_STR",menu,"remstr")
    await get_int_variable("TG_UP_LIMIT",menu,"tguplimit")

    if edit:
        rmess = await e.edit(header+"\nIts recommended to lock the group before setting vars.\n"+msg,parse_mode="html",buttons=menu)
    else:
        rmess = await e.reply(header+"\nIts recommended to lock the group before setting vars.\n",parse_mode="html",buttons=menu)

# an attempt to manager all the input
async def general_input_manager(e,mmes,var_name,datatype,value,db):
    if value is not None:
        await confirm_buttons(mmes,value)
        conf = await get_confirm(e)
        if conf is not None:
            if conf:
                try:
                    if datatype == "int":
                        value = int(value)
                    if datatype == "str":
                        value = str(value)
                    if datatype == "bool":
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        else:
                            raise ValueError("Invalid value from bool")
                        
                    db.set_variable(var_name,value)
                    await handle_settings(mmes,True,f"<b><u>Received {var_name} value '{value}' with confirm.</b></u>")
                except ValueError:
                    await handle_settings(mmes,True,f"<b><u>Value [{value}] not valid try again and enter {datatype}.</b></u>")    
            else:
                await handle_settings(mmes,True,f"<b><u>Confirm differed by user.</b></u>")
        else:
            await handle_settings(mmes,True,f"<b><u>Confirm timed out [waited 60s for input].</b></u>")
    else:
        await handle_settings(mmes,True,f"<b><u>Entry Timed out [waited 60s for input].</b></u>")


async def get_value(e):
    # this function gets the new value to be set from the user in current context
    lis = [False,None]
    #func tools works as expected ;);)
        
    cbak = partial(val_input_callback,lis=lis)
    
    e.client.add_event_handler(
        #lambda e: test_callback(e,lis),
        cbak,
        events.NewMessage()
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break

        await aio.sleep(1)
    
    val = lis[1]
    
    e.client.remove_event_handler(cbak)

    return val

async def get_confirm(e):
    # abstract for getting the confirm in a context

    lis = [False,None]
    cbak = partial(get_confirm_callback,lis=lis)
    
    e.client.add_event_handler(
        #lambda e: test_callback(e,lis),
        cbak,
        events.CallbackQuery(pattern="confirmsetting")
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break
        await aio.sleep(1)

    val = lis[1]
    
    e.client.remove_event_handler(cbak)

    return val

async def val_input_callback(e,lis):
    # get the input value
    lis[0] = True
    lis[1] = e.text
    await e.delete()
    raise events.StopPropagation

async def get_confirm_callback(e,lis):
    # handle the confirm callback
    lis[0] = True
    
    data = e.data.decode().split(" ")
    if data[1] == "true":
        lis[1] = True
    else:
        lis[1] = False

async def confirm_buttons(e,val):
    # add the confirm buttons at the bottom of the message
    await e.edit(f"Confirm the input :- <u>{val}</u>",buttons=[KeyboardButtonCallback("Yes","confirmsetting true"),KeyboardButtonCallback("No","confirmsetting false")],parse_mode="html")

async def get_bool_variable(var_name,msg,menu,callback_name):
    # handle the vars having bool values
     
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
    # handle the vars having string value

    val = get_val(var_name)
    msg = var_name + " " + val
    menu.append(
        [KeyboardButtonCallback(msg,f"settings {callback_name}".encode("UTF-8"))]
    ) 

async def get_int_variable(var_name,menu,callback_name):
    # handle the vars having string value

    val = get_val(var_name)
    msg = var_name + " " + str(val)
    menu.append(
        [KeyboardButtonCallback(msg,f"settings {callback_name}".encode("UTF-8"))]
    ) 

# todo handle the list value 