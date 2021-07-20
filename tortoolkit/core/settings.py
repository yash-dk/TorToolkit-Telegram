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

from telethon import events
from telethon.tl.types import KeyboardButtonCallback

from tortoolkit import SessionVars

from .database_handle import TorToolkitDB
from .getVars import get_val

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
header = '<b>TorToolKitX by <a href="https://github.com/XcodersHub/TorToolkitX">XcodersHub</a></b>\n<u>ADMIN SETTINGS MENU - Beta v1</u>'


async def handle_setting_callback(e):
    db = tordb
    session_id, _ = db.get_variable("SETTING_AUTH_CODE")

    data = e.data.decode()
    cmd = data.split(" ")
    val = ""

    if cmd[-1] != session_id:
        print("Session id", session_id, " - - ", cmd[-1])
        await e.answer("This Setting menu is expired.", alert=True)
        await e.delete()
        return
    if cmd[1] == "fdocs":
        await e.answer("")
        if cmd[2] == "true":
            val = True
        else:
            val = False

        db.set_variable("FORCE_DOCUMENTS", val)
        SessionVars.update_var("FORCE_DOCUMENTS", val)
        await handle_settings(
            await e.get_message(),
            True,
            f"<b><u>Changed the value to {val} of force documents.</b></u>",
            session_id=session_id,
        )

    elif cmd[1] == "compstr":
        await e.answer(
            "Type the new value for Complete Progress String. Note that only one character is expected.",
            alert=True,
        )

        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e)

        await general_input_manager(e, mmes, "COMPLETED_STR", "str", val[0], db, None)

    elif cmd[1] == "remstr":
        # what will a general manager require
        # anser message, type handler, value
        await e.answer(
            "Type the new value for Remaining Progress String. Note that only one character is expected.",
            alert=True,
        )

        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e)

        await general_input_manager(e, mmes, "REMAINING_STR", "str", val[0], db, None)

    elif cmd[1] == "tguplimit":
        # what will a general manager require
        # anser message, type handler, value
        await e.answer(
            "Type the new value for TELEGRAM UPLOAD LIMIT. Note that integer is expected.",
            alert=True,
        )

        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e)

        await general_input_manager(e, mmes, "TG_UP_LIMIT", "int", val, db, None)

    elif cmd[1] == "maxtorsize":
        # what will a general manager require
        # answer message, type handler, value
        await e.answer(
            "Type the new value for MAX TORRENT SIZE. Note that integer is expected.",
            alert=True,
        )

        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e)

        await general_input_manager(e, mmes, "MAX_TORRENT_SIZE", "int", val, db, None)

    elif cmd[1] == "maxytplsize":
        # what will a general manager require
        # answer message, type handler, value
        await e.answer(
            "Type the new value for MAX PLAYLIST SIZE. Note that integer is expected.",
            alert=True,
        )

        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e)

        await general_input_manager(
            e, mmes, "MAX_YTPLAYLIST_SIZE", "int", val, db, None
        )

    elif cmd[1] == "rclonemenu":
        # this is menu
        mmes = await e.get_message()
        await handle_settings(
            mmes,
            True,
            "\nWelcome to Rclone Config Menu. TD= Team Drive, ND= Normal Drive",
            submenu="rclonemenu",
            session_id=session_id,
        )
    elif cmd[1] == "mainmenu":
        # this is menu
        mmes = await e.get_message()
        await handle_settings(mmes, True, session_id=session_id)
    elif cmd[1] == "rcloneconfig":
        await e.answer(
            "Sned the rclone config file which you have generated.", alert=True
        )
        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e, True)

        await general_input_manager(
            e, mmes, "RCLONE_CONFIG", "str", val, db, "rclonemenu"
        )
    elif cmd[1] == "change_drive":
        await e.answer(f"Changed default drive to {cmd[2]}.", alert=True)
        db.set_variable("DEF_RCLONE_DRIVE", cmd[2])
        SessionVars.update_var("DEF_RCLONE_DRIVE", cmd[2])

        await handle_settings(
            await e.get_message(),
            True,
            f"<b><u>Changed the default drive to {cmd[2]}</b></u>",
            "rclonemenu",
            session_id=session_id,
        )
    elif cmd[1] == "usrlock":
        if cmd[2] == "true":
            val = True
            try:
                # JIC is user does manual stuff
                await e.client.edit_permissions(e.chat_id, send_messages=False)
            except:
                await e.answer(
                    "An error occured try again if dosent work report this issue"
                )
        else:
            try:
                await e.client.edit_permissions(e.chat_id, send_messages=True)
            except:
                await e.answer(
                    "An error occured try again if dosent work report this issue"
                )
            val = False

        db.set_variable("LOCKED_USERS", val)
        SessionVars.update_var("LOCKED_USERS", val)
        await handle_settings(
            await e.get_message(),
            True,
            f"<b><u>Changed the value to {val} of user locked.</b></u>",
            session_id=session_id,
        )

    elif cmd[1] == "ctrlacts":
        # this is menu
        mmes = await e.get_message()
        await handle_settings(
            mmes,
            True,
            "\nWelcome to Control Actions.",
            submenu="ctrlacts",
            session_id=session_id,
        )

    elif cmd[1] == "rcloneenable":
        await e.answer(
            "Note that this parameter will only work if rclone config is loaded."
        )
        if cmd[2] == "true":
            val = True
        else:
            val = False
        db.set_variable("RCLONE_ENABLED", val)
        SessionVars.update_var("RCLONE_ENABLED", val)
        mmes = await e.get_message()
        await handle_settings(
            mmes,
            True,
            f"<b><u>Changed the value to {val} of Rclone Enabled.</b></u>",
            "ctrlacts",
            session_id=session_id,
        )

    elif cmd[1] == "leechenable":
        await e.answer("")
        if cmd[2] == "true":
            val = True
        else:
            val = False

        db.set_variable("LEECH_ENABLED", val)
        SessionVars.update_var("LEECH_ENABLED", val)
        mmes = await e.get_message()
        await handle_settings(
            mmes,
            True,
            f"<b><u>Changed the value to {val} of Leech Enabled.</b></u>",
            "ctrlacts",
            session_id=session_id,
        )

    elif cmd[1] == "editsleepsec":
        await e.answer(
            "Type the new value for EDIT_SLEEP_SECS. Note that integer is expected.",
            alert=True,
        )

        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e)

        await general_input_manager(e, mmes, "EDIT_SLEEP_SECS", "int", val, db, None)
    elif cmd[1] == "statusdeltime":
        await e.answer(
            "Type the new value for STATUS_DEL_TOUT. Note that integer is expected.",
            alert=True,
        )

        mmes = await e.get_message()
        await mmes.edit(f"{mmes.raw_text}\n/ignore to go back", buttons=None)
        val = await get_value(e)

        await general_input_manager(e, mmes, "STATUS_DEL_TOUT", "int", val, db, None)
    elif cmd[1] == "fastupload":
        await e.answer("")

        if cmd[2] == "true":
            val = True
        else:
            val = False

        db.set_variable("FAST_UPLOAD", val)
        SessionVars.update_var("FAST_UPLOAD", val)
        mmes = await e.get_message()
        await handle_settings(
            mmes,
            True,
            f"<b><u>Changed the value to {val} of Fast Upload Enabled.</b></u>",
            "ctrlacts",
            session_id=session_id,
        )
    elif cmd[1] == "expressupload":
        await e.answer("")

        if cmd[2] == "true":
            val = True
        else:
            val = False

        db.set_variable("EXPRESS_UPLOAD", val)
        SessionVars.update_var("EXPRESS_UPLOAD", val)
        mmes = await e.get_message()
        await handle_settings(
            mmes,
            True,
            f"<b><u>Changed the value to {val} of Express Upload Enabled.</b></u>",
            "ctrlacts",
            session_id=session_id,
        )
    elif cmd[1] == "allowuset":
        await e.answer("")

        if cmd[2] == "true":
            val = True
        else:
            val = False

        db.set_variable("USETTINGS_IN_PRIVATE", val)
        SessionVars.update_var("USETTINGS_IN_PRIVATE", val)
        mmes = await e.get_message()
        await handle_settings(
            mmes,
            True,
            f"<b><u>Changed the value to {val} of Allow USETTINGS IN PRIVATE.</b></u>",
            "ctrlacts",
            session_id=session_id,
        )
    elif cmd[1] == "metainfo":
        await e.reply("Add @metainforobot to your group to get the metadata easily.")
    elif cmd[1] == "selfdest":
        await e.answer("Closed")
        await e.delete()


async def handle_settings(e, edit=False, msg="", submenu=None, session_id=None):
    # this function creates the menu
    # and now submenus too
    # REMOVED HEROKU BLOCK
    if session_id is None:
        session_id = time.time()
        db = tordb
        db.set_variable("SETTING_AUTH_CODE", str(session_id))
        SessionVars.update_var("SETTING_AUTH_CODE", str(session_id))

    menu = [
        # [KeyboardButtonCallback(yes+" Allow TG Files Leech123456789-","settings data".encode("UTF-8"))], # for ref
    ]

    if submenu is None:
        await get_bool_variable(
            "LOCKED_USERS", "Lock the Group", menu, "usrlock", session_id
        )
        await get_bool_variable(
            "FORCE_DOCUMENTS", "FORCE_DOCUMENTS", menu, "fdocs", session_id
        )
        await get_bool_variable(
            "METAINFO_BOT",
            "[MetainfoRoBot]Get metadata of files in this group.",
            menu,
            "metainfo",
            session_id,
        )
        await get_string_variable("COMPLETED_STR", menu, "compstr", session_id)
        await get_string_variable("REMAINING_STR", menu, "remstr", session_id)
        await get_int_variable("TG_UP_LIMIT", menu, "tguplimit", session_id)
        await get_int_variable("MAX_TORRENT_SIZE", menu, "maxtorsize", session_id)
        await get_int_variable("MAX_YTPLAYLIST_SIZE", menu, "maxytplsize", session_id)
        await get_int_variable("EDIT_SLEEP_SECS", menu, "editsleepsec", session_id)
        await get_int_variable("STATUS_DEL_TOUT", menu, "statusdeltime", session_id)
        # await get_string_variable("RCLONE_CONFIG",menu,"rcloneconfig",session_id)
        await get_sub_menu("☁️ Open Rclone Menu ☁️", "rclonemenu", session_id, menu)
        await get_sub_menu("🕹️ Control Actions 🕹️", "ctrlacts", session_id, menu)
        menu.append(
            [
                KeyboardButtonCallback(
                    "Close Menu", f"settings selfdest {session_id}".encode("UTF-8")
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
        else:
            rmess = await e.reply(
                header + "\nIts recommended to lock the group before setting vars.\n",
                parse_mode="html",
                buttons=menu,
                link_preview=False,
            )
    elif submenu == "rclonemenu":
        rcval = await get_string_variable(
            "RCLONE_CONFIG", menu, "rcloneconfig", session_id
        )
        if rcval != "None":
            # create a all drives menu
            if rcval == "Custom file is loaded.":
                db = tordb
                _, fdata = db.get_variable("RCLONE_CONFIG")

                path = os.path.join(os.getcwd(), "rclone.conf")

                # find alternative to this
                with open(path, "wb") as fi:
                    fi.write(fdata)

                conf = configparser.ConfigParser()
                conf.read(path)
                # menu.append([KeyboardButton("Choose a default drive from below")])
                def_drive = get_val("DEF_RCLONE_DRIVE")

                for j in conf.sections():
                    prev = ""
                    if j == def_drive:
                        prev = yes

                    if "team_drive" in list(conf[j]):
                        menu.append(
                            [
                                KeyboardButtonCallback(
                                    f"{prev}{j} - TD",
                                    f"settings change_drive {j} {session_id}",
                                )
                            ]
                        )
                    else:
                        menu.append(
                            [
                                KeyboardButtonCallback(
                                    f"{prev}{j} - ND",
                                    f"settings change_drive {j} {session_id}",
                                )
                            ]
                        )

        await get_sub_menu("Go Back ⬅️", "mainmenu", session_id, menu)
        menu.append(
            [
                KeyboardButtonCallback(
                    "Close Menu", f"settings selfdest {session_id}".encode("UTF-8")
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

    elif submenu == "ctrlacts":
        await get_bool_variable(
            "RCLONE_ENABLED", "Enable Rclone.", menu, "rcloneenable", session_id
        )
        await get_bool_variable(
            "LEECH_ENABLED", "Enable Leech.", menu, "leechenable", session_id
        )
        await get_bool_variable(
            "USETTINGS_IN_PRIVATE",
            "Usettings in private.",
            menu,
            "allowuset",
            session_id,
        )
        await get_bool_variable(
            "FAST_UPLOAD",
            "Enable Fast Upload.(Turn off if errored)",
            menu,
            "fastupload",
            session_id,
        )
        await get_bool_variable(
            "EXPRESS_UPLOAD",
            "Enable Express Upload.(read README on github for more info)(Turn off if errored)",
            menu,
            "expressupload",
            session_id,
        )
        await get_bool_variable(
            "FORCE_DOCS_USER",
            "Not Implemented.User will choose force docs.",
            menu,
            "forcedocsuser",
            session_id,
        )

        await get_sub_menu("Go Back ⬅️", "mainmenu", session_id, menu)
        menu.append(
            [
                KeyboardButtonCallback(
                    "Close Menu", f"settings selfdest {session_id}".encode("UTF-8")
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


# REMOVED HEROKU BLOCK

# an attempt to manager all the input
async def general_input_manager(e, mmes, var_name, datatype, value, db, sub_menu):
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
                                db.set_variable("DEF_RCLONE_DRIVE", str(i))
                                SessionVars.update_var("DEF_RCLONE_DRIVE", str(i))
                                break

                            with open(value, "rb") as fi:
                                data = fi.read()
                                db.set_variable("RCLONE_CONFIG", 0, True, data)
                            os.remove(value)
                            db.set_variable("LEECH_ENABLED", True)
                            SessionVars.update_var("LEECH_ENABLED", True)
                        except Exception:
                            torlog.error(traceback.format_exc())
                            await handle_settings(
                                mmes,
                                True,
                                f"<b><u>The conf file is invalid check logs.</b></u>",
                                sub_menu,
                            )
                            return
                    else:
                        db.set_variable(var_name, value)
                        SessionVars.update_var(var_name, value)

                    await handle_settings(
                        mmes,
                        True,
                        f"<b><u>Received {var_name} value '{value}' with confirm.</b></u>",
                        sub_menu,
                    )
                except ValueError:
                    await handle_settings(
                        mmes,
                        True,
                        f"<b><u>Value [{value}] not valid try again and enter {datatype}.</b></u>",
                        sub_menu,
                    )
            else:
                await handle_settings(
                    mmes, True, f"<b><u>Confirm differed by user.</b></u>", sub_menu
                )
        else:
            await handle_settings(
                mmes,
                True,
                f"<b><u>Confirm timed out [waited 60s for input].</b></u>",
                sub_menu,
            )
    else:
        await handle_settings(
            mmes,
            True,
            f"<b><u>Entry Timed out [waited 60s for input]. OR else ignored.</b></u>",
            sub_menu,
        )


async def get_value(e, file=False):
    # todo replace with conver. - or maybe not Fix Dont switch to conversion
    # this function gets the new value to be set from the user in current context
    lis = [False, None]

    # func tools works as expected ;);)
    cbak = partial(val_input_callback, o_sender=e.sender_id, lis=lis, file=file)

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


async def val_input_callback(e, o_sender, lis, file):
    # get the input value
    if o_sender != e.sender_id:
        return
    if not file:
        lis[0] = True
        lis[1] = e.text
        await e.delete()
    else:
        if e.document is not None:
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


async def get_bool_variable(var_name, msg, menu, callback_name, session_id):
    # handle the vars having bool values

    val = get_val(var_name)

    if val:
        # setting the value in callback so calls will be reduced ;)
        menu.append(
            [
                KeyboardButtonCallback(
                    yes + msg,
                    f"settings {callback_name} false {session_id}".encode("UTF-8"),
                )
            ]
        )
    else:
        menu.append(
            [
                KeyboardButtonCallback(
                    no + msg,
                    f"settings {callback_name} true {session_id}".encode("UTF-8"),
                )
            ]
        )


async def get_sub_menu(msg, sub_name, session_id, menu):
    menu.append(
        [
            KeyboardButtonCallback(
                msg, f"settings {sub_name} {session_id}".encode("UTF-8")
            )
        ]
    )


async def get_string_variable(var_name, menu, callback_name, session_id):
    # handle the vars having string value
    # condition for rclone config

    val = get_val(var_name)
    if var_name == "RCLONE_CONFIG":
        db = tordb
        _, val1 = db.get_variable(var_name)
        if val1 is not None:
            val = "Custom file is loaded."
        else:
            val = "Click here to load RCLONE config."

    msg = var_name + " " + str(val)
    menu.append(
        [
            KeyboardButtonCallback(
                msg, f"settings {callback_name} {session_id}".encode("UTF-8")
            )
        ]
    )

    # Just in case
    return val


async def get_int_variable(var_name, menu, callback_name, session_id):
    # handle the vars having string value

    val = get_val(var_name)
    msg = var_name + " " + str(val)
    menu.append(
        [
            KeyboardButtonCallback(
                msg, f"settings {callback_name} {session_id}".encode("UTF-8")
            )
        ]
    )


# todo handle the list value
