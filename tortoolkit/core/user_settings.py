# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio as aio
import configparser
import logging
import os
import time
import traceback
from functools import partial

from PIL import Image
from telethon import events
from telethon.tl.types import KeyboardButtonCallback

from .. import user_db
from .database_handle import TorToolkitDB

torlog = logging.getLogger(__name__)
# logging.getLogger("telethon").setLevel(logging.DEBUG)

TIMEOUT_SEC = 60

# this file will contian all the handlers and code for settings
# code can be more modular i think but not bothering now
# todo make the code more modular
no = "❌"
yes = "✅"
# Central object is not used its Acknowledged
tordb = TorToolkitDB()
header = '<b>TorToolKitX by <a href="https://github.com/XcodersHub/TorToolkitX">XcodersHub</a></b>\n<u>USER SETTINGS MENU - v1</u>'


async def handle_user_setting_callback(e):
    sender_id = str(e.sender_id)

    data = e.data.decode()
    cmd = data.split(" ")

    val = ""

    if cmd[-1] != sender_id:
        print("Sender id", sender_id, " - - ", cmd[-1])
        await e.answer("Dont touch sender dosent match.", alert=True)
        # await e.delete()
        return
    if cmd[1] == "mycmd":
        pass
    elif cmd[1] == "rclonemenu":
        # this is menu
        mmes = await e.get_message()
        await handle_user_settings(
            mmes,
            True,
            "\nWelcome to Rclone Config Menu. TD= Team Drive, ND= Normal Drive",
            submenu="rclonemenu",
            sender_id=sender_id,
        )
    elif cmd[1] == "thumbmenu":
        # this is menu
        mmes = await e.get_message()
        await handle_user_settings(
            mmes,
            True,
            "\nWelcome to Thumbnail Menu.",
            submenu="thumbmenu",
            sender_id=sender_id,
        )
    elif cmd[1] == "rcloneconfig":
        await e.answer(
            "Send the rclone config file which you have generated.", alert=True
        )
        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e, True)

        await general_input_manager(
            e, mmes, "RCLONE_CONFIG", "str", val, sender_id, "rclonemenu"
        )
    elif cmd[1] == "setthumb":
        await e.answer("Send the thumbnail.", alert=True)
        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n /ignore to go back.", buttons=None)
        val = await get_value(e, file=True, photo=True)
        await general_input_manager(
            e, mmes, "THUMBNAIL", "str", val, sender_id, "thumbmenu"
        )

    elif cmd[1] == "selfdest":
        await e.answer("Closed")
        await e.delete()
    elif cmd[1] == "change_drive":
        await e.answer(f"Changed default drive to {cmd[2]}.", alert=True)
        user_db.set_var("DEF_RCLONE_DRIVE", str(cmd[2]), e.sender_id)

        await handle_user_settings(
            await e.get_message(),
            True,
            f"<b><u>Changed the default drive to {cmd[2]}</b></u>",
            "rclonemenu",
            sender_id=sender_id,
        )
    elif cmd[1] == "mainmenu":
        # this is menu
        mmes = await e.get_message()
        await handle_user_settings(mmes, True, sender_id=sender_id)
    elif cmd[1] == "fdocs":
        await e.answer("")
        if cmd[2] == "true":
            val = True
        else:
            val = False

        user_db.set_var("FORCE_DOCUMENTS", val, str(e.sender_id))
        await handle_user_settings(
            await e.get_message(),
            True,
            f"<b><u>Changed the value to {val} of force documents.</b></u>",
            sender_id=sender_id,
        )
    elif cmd[1] == "disablethumb":
        await e.answer("")
        if cmd[2] == "true":
            val = True
        else:
            val = False

        user_db.set_var("DISABLE_THUMBNAIL", val, str(e.sender_id))
        await handle_user_settings(
            await e.get_message(),
            True,
            f"<b><u>Changed the value to {val} of disable thumbnail.</b></u>",
            sender_id=sender_id,
            submenu="thumbmenu",
        )


async def handle_user_settings(e, edit=False, msg="", submenu=None, sender_id=None):
    # this function creates the menu
    # and now submenus too
    if sender_id is None:
        sender_id = e.sender_id

    menu = [
        # [KeyboardButtonCallback(yes+" Allow TG Files Leech123456789-","settings data".encode("UTF-8"))], # for ref
    ]

    if submenu is None:
        await get_bool_variable(
            "FORCE_DOCUMENTS", "FORCE_DOCUMENTS", menu, "fdocs", sender_id
        )  #
        # await get_string_variable("RCLONE_CONFIG",menu,"rcloneconfig",session_id)
        await get_sub_menu("☁️ Open Rclone Menu ☁️", "rclonemenu", sender_id, menu)  #
        await get_sub_menu("🖼 Open Thumbnail Menu 🖼", "thumbmenu", sender_id, menu)  #
        # thumbnail
        menu.append(
            [
                KeyboardButtonCallback(
                    "Close Menu", f"usettings selfdest {sender_id}".encode("UTF-8")
                )
            ]
        )

        if edit:
            rmess = await e.edit(
                header + "\nEnjoiii.\n" + msg,
                parse_mode="html",
                buttons=menu,
                link_preview=False,
                file="toolkit.jpg",
            )
        else:
            rmess = await e.reply(
                header + "\nEnjoiii.\n",
                parse_mode="html",
                buttons=menu,
                link_preview=False,
                file="toolkit.jpg",
            )
    elif submenu == "rclonemenu":
        rcval = await get_string_variable(
            "RCLONE_CONFIG", menu, "rcloneconfig", sender_id
        )
        if rcval != "None":
            # create a all drives menu
            if not "not loaded" in rcval:

                path = user_db.get_rclone(sender_id)

                conf = configparser.ConfigParser()
                conf.read(path)
                # menu.append([KeyboardButton("Choose a default drive from below")])
                def_drive = user_db.get_var("DEF_RCLONE_DRIVE", sender_id)

                for j in conf.sections():
                    prev = ""
                    if j == def_drive:
                        prev = yes

                    if "team_drive" in list(conf[j]):
                        menu.append(
                            [
                                KeyboardButtonCallback(
                                    f"{prev}{j} - TD",
                                    f"usettings change_drive {j} {sender_id}",
                                )
                            ]
                        )
                    else:
                        menu.append(
                            [
                                KeyboardButtonCallback(
                                    f"{prev}{j} - ND",
                                    f"usettings change_drive {j} {sender_id}",
                                )
                            ]
                        )

        await get_sub_menu("Go Back ⬅️", "mainmenu", sender_id, menu)
        menu.append(
            [
                KeyboardButtonCallback(
                    "Close Menu", f"usettings selfdest {sender_id}".encode("UTF-8")
                )
            ]
        )
        if edit:
            rmess = await e.edit(
                header
                + "\nIts recommended to lock the group before setting vars.\n"
                + msg,
                parse_mode="html",
                buttons=menu,
                link_preview=False,
            )

    elif submenu == "thumbmenu":
        thumb = user_db.get_thumbnail(sender_id)
        if thumb is not False:
            menu.append(
                [
                    KeyboardButtonCallback(
                        "Change Thumbnail",
                        f"usettings setthumb {sender_id}".encode("UTF-8"),
                    )
                ]
            )
            await get_bool_variable(
                "DISABLE_THUMBNAIL",
                "Disable Thumbnail",
                menu,
                "disablethumb",
                sender_id,
            )
            await get_sub_menu("Go Back ⬅️", "mainmenu", sender_id, menu)
            menu.append(
                [
                    KeyboardButtonCallback(
                        "Close Menu", f"usettings selfdest {sender_id}".encode("UTF-8")
                    )
                ]
            )
            await e.edit(
                header + "\nManage your thumbnail(s) on the fly.",
                file=thumb,
                buttons=menu,
                parse_mode="html",
            )
        else:
            menu.append(
                [
                    KeyboardButtonCallback(
                        "Set Thumbnail.",
                        f"usettings setthumb {sender_id}".encode("UTF-8"),
                    )
                ]
            )
            await get_sub_menu("Go Back ⬅️", "mainmenu", sender_id, menu)
            menu.append(
                [
                    KeyboardButtonCallback(
                        "Close Menu", f"usettings selfdest {sender_id}".encode("UTF-8")
                    )
                ]
            )
            await e.edit(
                header + "\nManage your thumbnail(s) on the fly.",
                parse_mode="html",
                buttons=menu,
            )


# an attempt to manager all the input
async def general_input_manager(
    e, mmes, var_name, datatype, value, sender_id, sub_menu
):
    if value is not None and not "ignore" in value:
        await confirm_buttons(mmes, value)
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

                    if var_name == "RCLONE_CONFIG":
                        # adjust the special case
                        try:
                            conf = configparser.ConfigParser()
                            conf.read(value)
                            for i in conf.sections():
                                user_db.set_var("DEF_RCLONE_DRIVE", str(i), e.sender_id)
                                break

                            with open(value, "rb") as fi:
                                data = fi.read()
                                user_db.set_rclone(data, e.sender_id)
                            os.remove(value)
                            # db.set_variable("LEECH_ENABLED",True)
                            # SessionVars.update_var("LEECH_ENABLED",True)
                        except Exception:
                            torlog.error(traceback.format_exc())
                            await handle_user_settings(
                                mmes,
                                True,
                                f"<b><u>The conf file is invalid check logs.</b></u>",
                                sub_menu,
                            )
                            return
                    elif var_name == "THUMBNAIL":
                        try:
                            im = Image.open(value)
                            im.convert("RGB").save(value, "JPEG")
                            im = Image.open(value)
                            im.thumbnail((320, 320), Image.ANTIALIAS)
                            im.save(value, "JPEG")
                            with open(value, "rb") as fi:
                                data = fi.read()
                                user_db.set_thumbnail(data, e.sender_id)
                            os.remove(value)
                        except Exception:
                            torlog.error(traceback.format_exc())
                            await handle_user_settings(
                                mmes,
                                True,
                                f"<b><u>Error in the thumbnail you sent.</b></u>",
                                sub_menu,
                            )
                            return
                    else:
                        user_db.set_var(var_name, value, e.sender_id)
                        # db.set_variable(var_name,value)
                        # SessionVars.update_var(var_name,value)

                    await handle_user_settings(
                        mmes,
                        True,
                        f"<b><u>Received {var_name} value '{value}' with confirm.</b></u>",
                        sub_menu,
                        sender_id=sender_id,
                    )
                except ValueError:
                    await handle_user_settings(
                        mmes,
                        True,
                        f"<b><u>Value [{value}] not valid try again and enter {datatype}.</b></u>",
                        sub_menu,
                        sender_id=sender_id,
                    )
            else:
                await handle_user_settings(
                    mmes,
                    True,
                    f"<b><u>Confirm differed by user.</b></u>",
                    sub_menu,
                    sender_id=sender_id,
                )
        else:
            await handle_user_settings(
                mmes,
                True,
                f"<b><u>Confirm timed out [waited 60s for input].</b></u>",
                sub_menu,
                sender_id=sender_id,
            )
    else:
        await handle_user_settings(
            mmes,
            True,
            f"<b><u>Entry Timed out [waited 60s for input]. OR else ignored.</b></u>",
            sub_menu,
            sender_id=sender_id,
        )


async def get_value(e, file=False, photo=False):
    # todo replace with conver. - or maybe not Fix Dont switch to conversion
    # this function gets the new value to be set from the user in current context
    lis = [False, None]

    # func tools works as expected ;);)
    cbak = partial(
        val_input_callback, o_sender=e.sender_id, lis=lis, file=file, photo=photo
    )

    e.client.add_event_handler(
        # lambda e: test_callback(e,lis),
        cbak,
        events.NewMessage(),
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

    lis = [False, None]
    cbak = partial(get_confirm_callback, o_sender=e.sender_id, lis=lis)

    e.client.add_event_handler(
        # lambda e: test_callback(e,lis),
        cbak,
        events.CallbackQuery(pattern="confirmsetting"),
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break
        await aio.sleep(1)

    val = lis[1]

    e.client.remove_event_handler(cbak)

    return val


async def val_input_callback(e, o_sender, lis, file, photo):
    # get the input value
    if o_sender != e.sender_id:
        return
    if not file and not photo:
        lis[0] = True
        lis[1] = e.text
        await e.delete()
    else:
        if e.document is not None and file:
            path = await e.download_media()
            lis[0] = True
            lis[1] = path
            await e.delete()
        elif e.photo is not None and photo:
            path = await e.download_media()
            lis[0] = True
            lis[1] = path
            await e.delete()

        else:
            if "ignore" in e.text:
                lis[0] = True
                lis[1] = "ignore"
                await e.delete()
            else:
                await e.delete()

    raise events.StopPropagation


async def get_confirm_callback(e, o_sender, lis):
    # handle the confirm callback

    if o_sender != e.sender_id:
        return
    lis[0] = True

    data = e.data.decode().split(" ")
    if data[1] == "true":
        lis[1] = True
    else:
        lis[1] = False


async def confirm_buttons(e, val):
    # add the confirm buttons at the bottom of the message
    await e.edit(
        f"Confirm the input :- <u>{val}</u>",
        buttons=[
            KeyboardButtonCallback("Yes", "confirmsetting true"),
            KeyboardButtonCallback("No", "confirmsetting false"),
        ],
        parse_mode="html",
    )


async def get_bool_variable(var_name, msg, menu, callback_name, sender_id):
    # handle the vars having bool values

    val = user_db.get_var(var_name, sender_id)
    try:
        val = bool(val)
    except:
        val = False
    if val:
        # setting the value in callback so calls will be reduced ;)
        menu.append(
            [
                KeyboardButtonCallback(
                    yes + msg,
                    f"usettings {callback_name} false {sender_id}".encode("UTF-8"),
                )
            ]
        )
    else:
        menu.append(
            [
                KeyboardButtonCallback(
                    no + msg,
                    f"usettings {callback_name} true {sender_id}".encode("UTF-8"),
                )
            ]
        )


async def get_sub_menu(msg, sub_name, sender_id, menu):
    menu.append(
        [
            KeyboardButtonCallback(
                msg, f"usettings {sub_name} {sender_id}".encode("UTF-8")
            )
        ]
    )


async def get_string_variable(var_name, menu, callback_name, sender_id):
    # handle the vars having string value
    # condition for rclone config

    if var_name == "RCLONE_CONFIG":
        rfile = user_db.get_rclone(sender_id)
        if rfile is False:
            val = "File is not loaded."
        else:
            val = "File is Loaded"
            # val = "Custom file is loaded."
    else:
        val = user_db.get_var(var_name, sender_id)

    msg = var_name + " " + str(val)
    menu.append(
        [
            KeyboardButtonCallback(
                msg, f"usettings {callback_name} {sender_id}".encode("UTF-8")
            )
        ]
    )

    # Just in case
    return val


async def get_int_variable(var_name, menu, callback_name, sender_id):
    # handle the vars having string value

    val = user_db.get_var(var_name, sender_id)
    msg = var_name + " " + str(val)
    menu.append(
        [
            KeyboardButtonCallback(
                msg, f"usettings {callback_name} {sender_id}".encode("UTF-8")
            )
        ]
    )


# todo handle the list value
