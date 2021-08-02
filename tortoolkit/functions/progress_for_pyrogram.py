#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K + YashDK [yash-dk@github]

import asyncio

# the logging things
import logging
import math
import time

from ..core.getVars import get_val
from .Human_Format import human_readable_bytes, human_readable_timedelta

torlog = logging.getLogger(__name__)


async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start,
    time_out,
    client,
    cancel_msg=None,
    updb=None,
    markup=None,
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
            # IG Open stream will be Garbage Collected
            if updb.get_cancel_status(cancel_msg.chat.id, cancel_msg.message_id):
                print("Stopping transmission")
                client.stop_transmission()

        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        elapsed_time = round(diff)
        speed = current / elapsed_time
        time_to_completion = round((total - current) / speed)
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = human_readable_timedelta(elapsed_time)
        estimated_total_time = human_readable_timedelta(estimated_total_time)

        progress = "[{0}{1}] \nP: {2}%\n".format(
            "".join(
                [get_val("COMPLETED_STR") for _ in range(math.floor(percentage / 10))]
            ),
            "".join(
                [
                    get_val("REMAINING_STR")
                    for _ in range(10 - math.floor(percentage / 10))
                ]
            ),
            round(percentage, 2),
        )

        tmp = (
            progress
            + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\nUsing engine: Pyrogram".format(
                human_readable_bytes(current),
                human_readable_bytes(total),
                human_readable_bytes(speed),
                estimated_total_time if estimated_total_time != "" else "0 seconds",
            )
        )
        try:
            if not message.photo:
                await message.edit_text(
                    text="**Uploading:** `{}`\n{}".format(ud_type, tmp),
                    reply_markup=markup,
                )
            else:
                await message.edit_caption(
                    caption="**Uploading:** `{}`\n{}".format(ud_type, tmp),
                    reply_markup=markup,
                )
            await asyncio.sleep(4)
        except:
            pass
