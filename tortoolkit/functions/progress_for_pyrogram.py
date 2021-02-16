#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging

import math
import os
import time
from .Human_Format import human_readable_bytes,human_readable_timedelta
from ..core.getVars import get_val

torlog = logging.getLogger(__name__)

async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start,
    time_out,
    cancel_msg=None,
    updb=None
):
    now = time.time()
    diff = now - start
    
    # too early to update the progress
    if diff < 1:
        return
    
    if round(diff % time_out) == 0 or current == total:
        if cancel_msg is not None:
            # dirty alt. was not able to find something to stop upload
            # todo inspect with "StopAsyncIteration"
            if updb.get_cancel_status(cancel_msg.chat.id,cancel_msg.message_id):
                raise Exception("cancel the upload")
    
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        elapsed_time = round(diff)
        speed = current / elapsed_time
        time_to_completion = round((total - current) / speed)
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = time_formatter(elapsed_time)
        estimated_total_time = time_formatter(estimated_total_time)

        progress = "[{0}{1}] \nP: {2}%\n".format(
            ''.join([get_val("COMPLETED_STR") for _ in range(math.floor(percentage / 5))]),
            ''.join([get_val("REMAINING_STR") for _ in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            estimated_total_time if estimated_total_time != '' else "0 seconds"
        )
        try:
            if not message.photo:
                await message.edit_text(
                    text="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
            else:
                await message.edit_caption(
                    caption="{}\n {}".format(
                        ud_type,
                        tmp
                    )
                )
        except:
            pass


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def time_formatter(seconds: int) -> str:
    result = ""
    v_m = 0
    remainder = seconds
    r_ange_s = {
        "days": (24 * 60 * 60),
        "hours": (60 * 60),
        "minutes": 60,
        "seconds": 1
    }
    for age in r_ange_s:
        divisor = r_ange_s[age]
        v_m, remainder = divmod(remainder, divisor)
        v_m = int(v_m)
        if v_m != 0:
            result += f" {v_m} {age} "
    return result

