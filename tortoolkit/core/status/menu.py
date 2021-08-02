# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio
import logging
import time

from telethon.tl.types import KeyboardButtonCallback

from ... import to_del
from .status import ARTask, MegaDl, QBTask, Status
from .upload import RCUploadTask, TGUploadTask

torlog = logging.getLogger(__name__)


def get_num(no):
    nums = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    numstr = ""

    if no <= 9:
        return nums[no]
    else:
        for i in str(no):
            numstr += nums[int(i)]

    return numstr


async def create_status_menu(event):

    tasks = Status()
    tors = 0
    row = []
    Buttons = []

    msg = "<b>Currently Running:-<b/>\n<b>Click on the task No. that you want to cancel.</b>\n\n"
    for i in tasks.Tasks:
        if await i.is_active():

            msg += get_num(tors) + " " + await i.create_message()
            msg += "\n\n"
            try:
                if isinstance(i, QBTask):
                    omsg = await i.get_original_message()
                    data = "torcancel {} {}".format(i.hash, omsg.sender_id)
                if isinstance(i, ARTask):
                    data = "torcancel aria2 {} {}".format(
                        await i.get_gid(), await i.get_sender_id()
                    )
                if isinstance(i, MegaDl):
                    data = "torcancel megadl {} {}".format(
                        await i.get_gid(), await i.get_sender_id()
                    )
                if isinstance(i, TGUploadTask):
                    message = await i.get_message()
                    data = "upcancel {} {} {}".format(
                        message.chat_id, message.id, await i.get_sender_id()
                    )
                if isinstance(i, RCUploadTask):
                    omsg = await i.get_original_message()
                    data = "upcancel {} {} {}".format(
                        omsg.chat_id, omsg.id, omsg.sender_id
                    )
            except:
                torlog.exception("In status msg")
                tors += 1
                continue

            row.append(KeyboardButtonCallback(get_num(tors), data=data.encode("UTF-8")))
            if len(row) >= 4:
                Buttons.append(row)
                row = []

            tors += 1

    if row:
        Buttons.append(row)

    if not Buttons:
        Buttons = None

    if len(msg) > 3900:
        chunks, chunk_size = len(msg), 3900
        msgs = [msg[i : i + chunk_size] for i in range(0, chunks, chunk_size)]

        for j in msgs:
            memsg = await event.reply(j, parse_mode="html", buttons=Buttons)
            to_del.append([memsg, time.time()])
            await asyncio.sleep(1)
    else:
        memsg = await event.reply(msg, parse_mode="html", buttons=Buttons)
        to_del.append([memsg, time.time()])
    # memsg = await event.reply(msg,parse_mode="html", buttons=Buttons)
    # to_del.append([memsg, time.time()])


async def create_status_user_menu(event):

    tasks = Status()
    tors = 0
    row = []
    Buttons = []

    msg = "<b>Currently Running: For You:-</b> \n<b>Click on the task No. that you want to cancel.</b>\n\n"
    for i in tasks.Tasks:
        if await i.is_active():

            try:
                if isinstance(i, QBTask):
                    omsg = await i.get_original_message()
                    if not (event.sender_id == omsg.sender_id):
                        continue
                    data = "torcancel {} {}".format(i.hash, omsg.sender_id)
                if isinstance(i, MegaDl):
                    if not (event.sender_id == await i.get_sender_id()):
                        continue
                    data = "torcancel megadl {} {}".format(
                        await i.get_gid(), await i.get_sender_id()
                    )

                if isinstance(i, ARTask):
                    if not (event.sender_id == await i.get_sender_id()):
                        continue
                    data = "torcancel aria2 {} {}".format(
                        await i.get_gid(), await i.get_sender_id()
                    )
                if isinstance(i, TGUploadTask):
                    if not event.sender_id == await i.get_sender_id():
                        continue
                    message = await i.get_message()
                    data = "upcancel {} {} {}".format(
                        message.chat_id, message.id, await i.get_sender_id()
                    )
                if isinstance(i, RCUploadTask):
                    omsg = await i.get_original_message()
                    if not event.sender_id == omsg.sender_id:
                        continue
                    data = "upcancel {} {} {}".format(
                        omsg.chat_id, omsg.id, omsg.sender_id
                    )
            except:
                tors += 1
                torlog.exception("In status msg")
                continue

            msg += get_num(tors) + " " + await i.create_message()
            msg += "\n"

            row.append(KeyboardButtonCallback(get_num(tors), data=data.encode("UTF-8")))
            if len(row) >= 4:
                Buttons.append(row)
                row = []

            tors += 1

    if row:
        Buttons.append(row)

    if not Buttons:
        Buttons = None

    if len(msg) > 3900:
        chunks, chunk_size = len(msg), 3900
        msgs = [msg[i : i + chunk_size] for i in range(0, chunks, chunk_size)]

        for j in msgs:
            memsg = await event.reply(j, parse_mode="html", buttons=Buttons)
            to_del.append([memsg, time.time()])
            await asyncio.sleep(1)
    else:
        memsg = await event.reply(msg, parse_mode="html", buttons=Buttons)
        to_del.append([memsg, time.time()])

    # memsg = await event.reply(msg,parse_mode="html", buttons=Buttons)
    # to_del.append([memsg, time.time()])
