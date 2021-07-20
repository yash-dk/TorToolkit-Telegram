# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio as aio
import logging
import math
import os
from time import time

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

torlog = logging.getLogger(__name__)


async def gen_ss(filepath, ts, opfilepath=None):
    # todo check the error pipe and do processing
    source = filepath
    destination = os.path.dirname(source)
    ss_name = str(os.path.basename(source)) + "_" + str(round(time())) + ".jpg"
    ss_path = os.path.join(destination, ss_name)

    cmd = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-ss",
        str(ts),
        "-i",
        str(source),
        "-vframes",
        "1",
        "-q:v",
        "2",
        str(ss_path),
    ]

    subpr = await aio.create_subprocess_exec(
        *cmd, stdout=aio.subprocess.PIPE, stderr=aio.subprocess.PIPE
    )
    spipe, epipe = await subpr.communicate()
    epipe = epipe.decode().strip()
    spipe = spipe.decode().strip()
    torlog.info("Stdout Pipe :- {}".format(spipe))
    torlog.info("Error Pipe :- {}".format(epipe))

    return ss_path


async def resize_img(path, width=None, height=None):
    img = Image.open(path)
    wei, hei = img.size

    wei = width if width is not None else wei
    hei = height if height is not None else hei

    img.thumbnail((wei, hei))

    img.save(path, "JPEG")
    return path


async def split_file(path, max_size, force_docs=False):

    metadata = extractMetadata(createParser(path))

    if metadata.has("duration"):
        total_duration = metadata.get("duration").seconds

    metadata = metadata.exportDictionary()
    try:
        mime = metadata.get("Common").get("MIME type")
    except:
        mime = metadata.get("Metadata").get("MIME type")

    ftype = mime.split("/")[0]
    ftype = ftype.lower().strip()

    split_dir = os.path.join(os.path.dirname(path), str(time()))

    if not os.path.isdir(split_dir):
        os.makedirs(split_dir)

    if ftype == "video" and not force_docs:
        total_file_size = os.path.getsize(path)

        parts = math.ceil(total_file_size / max_size)
        # need this to be implemented to remove recursive file split calls
        # remove saftey margin
        # parts += 1
        torlog.info(f"Parts {parts}")

        minimum_duration = total_duration / parts

        # casting to int cuz float Time Stamp can cause errors
        minimum_duration = int(minimum_duration)
        torlog.info(f"Min dur :- {minimum_duration} total {total_duration}")

        # END: proprietary
        start_time = 0
        end_time = minimum_duration

        base_name = os.path.basename(path)
        input_extension = base_name.split(".")[-1]

        i = 0
        flag = False

        while end_time <= total_duration:

            # file name generate
            parted_file_name = "{}_PART_{}.{}".format(
                str(base_name), str(i).zfill(5), str(input_extension)
            )

            output_file = os.path.join(split_dir, parted_file_name)

            opfile = await cult_small_video(
                path, output_file, str(start_time), str(end_time)
            )
            torlog.info(f"Output file {opfile}")
            torlog.info(f"Start time {start_time}, End time {end_time}, Itr {i}")

            # adding offset of 3 seconds to ensure smooth playback
            start_time = end_time - 3
            end_time = end_time + minimum_duration
            i = i + 1

            if (end_time > total_duration) and not flag:
                end_time = total_duration
                flag = True
            elif i + 1 == parts:
                end_time = total_duration
                flag = True
            elif flag:
                break

    return split_dir


async def cult_small_video(video_file, out_put_file_name, start_time, end_time):
    file_genertor_command = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        video_file,
        "-ss",
        start_time,
        "-to",
        end_time,
        "-async",
        "1",
        "-strict",
        "-2",
        "-c",
        "copy",
        out_put_file_name,
    ]
    process = await aio.create_subprocess_exec(
        *file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=aio.subprocess.PIPE,
        stderr=aio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    stderr.decode().strip()
    stdout.decode().strip()
    return out_put_file_name
