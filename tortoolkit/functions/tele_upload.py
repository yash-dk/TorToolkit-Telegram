# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# (c) modified by AmirulAndalib [amirulandalib@github]

import asyncio
import logging
import os
import shutil
import time
import traceback

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaVideo,
)
from telethon.errors import VideoContentTypeInvalidError
from telethon.tl.types import KeyboardButtonCallback
from telethon.utils import get_attributes

from .. import user_db
from ..core import (
    thumb_manage,
)  # i guess i will dodge this one ;) as i am importing the vids helper anyways
from ..core.database_handle import TtkUpload
from ..core.getVars import get_val
from . import vids_helpers, zip7_utils
from .Ftele import upload_file
from .progress_for_pyrogram import progress_for_pyrogram
from .progress_for_telethon import progress

torlog = logging.getLogger(__name__)

# thanks @SpEcHiDe for this concept of recursion
async def upload_handel(
    path,
    message,
    from_uid,
    files_dict,
    job_id=0,
    force_edit=False,
    updb=None,
    from_in=False,
    thumb_path=None,
    user_msg=None,
    task=None,
):
    # creting here so connections are kept low
    if updb is None:
        # Central object is not used its Acknowledged
        updb = TtkUpload()

    # logging.info("Uploading Now:- {}".format(path))

    if os.path.isdir(path):
        logging.info("Uploading the directory:- {}".format(path))

        directory_contents = os.listdir(path)
        directory_contents.sort()
        try:
            # maybe way to refresh?!
            message = await message.client.get_messages(
                message.chat_id, ids=[message.id]
            )
            message = message[0]
        except:
            pass

        try:
            message = await message.edit(
                "{}\n\n**Found** {} **files for this Telegram Upload**".format(
                    message.text, len(directory_contents)
                )
            )
        except:
            torlog.warning("Too much folders will stop the editing of this message")

        if not from_in:
            updb.register_upload(message.chat_id, message.id)
            if user_msg is None:
                sup_mes = await message.get_reply_message()
            else:
                sup_mes = user_msg

            if task is not None:
                await task.set_message(message)
                await task.set_original_message(sup_mes)

            data = "upcancel {} {} {}".format(
                message.chat_id, message.id, sup_mes.sender_id
            )
            buts = [KeyboardButtonCallback("Cancel upload.", data.encode("UTF-8"))]
            message = await message.edit(buttons=buts)

        for file in directory_contents:
            if updb.get_cancel_status(message.chat_id, message.id):
                continue

            await upload_handel(
                os.path.join(path, file),
                message,
                from_uid,
                files_dict,
                job_id,
                force_edit,
                updb,
                from_in=True,
                thumb_path=thumb_path,
                user_msg=user_msg,
                task=task,
            )

        if not from_in:
            if updb.get_cancel_status(message.chat_id, message.id):
                task.cancel = True
                await task.set_inactive()
                await message.edit(
                    "{} - Canceled By user.".format(message.text), buttons=None
                )
            else:
                await message.edit(buttons=None)
            updb.deregister_upload(message.chat_id, message.id)

    else:
        logging.info("Uploading the file:- {}".format(path))
        if os.path.getsize(path) > get_val("TG_UP_LIMIT"):
            # the splitted file will be considered as a single upload ;)

            metadata = extractMetadata(createParser(path))

            if metadata is not None:
                # handle none for unknown
                metadata = metadata.exportDictionary()
                try:
                    mime = metadata.get("Common").get("MIME type")
                except:
                    mime = metadata.get("Metadata").get("MIME type")

                ftype = mime.split("/")[0]
                ftype = ftype.lower().strip()
            else:
                ftype = "unknown"

            if ftype == "video":
                todel = await message.reply(
                    "**FILE LARGER THAN 2GB, SPLITTING NOW...**\n**Using Algo FFMPEG VIDEO SPLIT**"
                )
                split_dir = await vids_helpers.split_file(path, get_val("TG_UP_LIMIT"))
                await todel.delete()
            else:
                todel = await message.reply(
                    "**FILE LARGER THAN 2GB, SPLITTING NOW...**\n**`Using Algo FFMPEG ZIP SPLIT`**"
                )
                split_dir = await zip7_utils.split_in_zip(path, get_val("TG_UP_LIMIT"))
                await todel.delete()

            if task is not None:
                await task.add_a_dir(split_dir)

            dircon = os.listdir(split_dir)
            dircon.sort()

            if not from_in:
                updb.register_upload(message.chat_id, message.id)
                if user_msg is None:
                    sup_mes = await message.get_reply_message()
                else:
                    sup_mes = user_msg

                if task is not None:
                    await task.set_message(message)
                    await task.set_original_message(sup_mes)

                data = "upcancel {} {} {}".format(
                    message.chat_id, message.id, sup_mes.sender_id
                )
                buts = [KeyboardButtonCallback("Cancel upload.", data.encode("UTF-8"))]
                await message.edit(buttons=buts)

            for file in dircon:
                if updb.get_cancel_status(message.chat_id, message.id):
                    continue

                await upload_handel(
                    os.path.join(split_dir, file),
                    message,
                    from_uid,
                    files_dict,
                    job_id,
                    force_edit,
                    updb=updb,
                    from_in=True,
                    thumb_path=thumb_path,
                    user_msg=user_msg,
                    task=task,
                )

            try:
                shutil.rmtree(split_dir)
                os.remove(path)
            except:
                pass

            if not from_in:
                if updb.get_cancel_status(message.chat_id, message.id):
                    task.cancel = True
                    await task.set_inactive()
                    await message.edit(
                        "{} - Canceled By user.".format(message.text), buttons=None
                    )
                else:
                    await message.edit(buttons=None)
                updb.deregister_upload(message.chat_id, message.id)
            # spliting file logic blah blah
        else:
            if not from_in:
                updb.register_upload(message.chat_id, message.id)
                if user_msg is None:
                    sup_mes = await message.get_reply_message()
                else:
                    sup_mes = user_msg

                if task is not None:
                    await task.set_message(message)
                    await task.set_original_message(sup_mes)

                if task is not None:
                    await task.set_message(message)
                    await task.set_original_message(sup_mes)

                data = "upcancel {} {} {}".format(
                    message.chat_id, message.id, sup_mes.sender_id
                )
                buts = [KeyboardButtonCallback("Cancel upload.", data.encode("UTF-8"))]
                await message.edit(buttons=buts)
            # print(updb)
            if black_list_exts(path):
                if task is not None:
                    await task.uploaded_file(os.path.basename(path))
                sentmsg = None
            else:
                sentmsg = await upload_a_file(
                    path, message, force_edit, updb, thumb_path, user_msg=user_msg
                )

            if not from_in:
                if updb.get_cancel_status(message.chat_id, message.id):
                    task.cancel = True
                    await task.set_inactive()
                    await message.edit(
                        "{} - Canceled By user.".format(message.text), buttons=None
                    )
                else:
                    await message.edit(buttons=None)
                updb.deregister_upload(message.chat_id, message.id)

            if sentmsg is not None:
                if task is not None:
                    await task.uploaded_file(os.path.basename(path))
                files_dict[os.path.basename(path)] = sentmsg.id

    return files_dict


async def upload_a_file(
    path, message, force_edit, database=None, thumb_path=None, user_msg=None
):
    if get_val("EXPRESS_UPLOAD"):
        return await upload_single_file(
            path, message, force_edit, database, thumb_path, user_msg
        )
    queue = message.client.queue
    if database is not None:
        if database.get_cancel_status(message.chat_id, message.id):
            # add os remove here
            return None
    if not os.path.exists(path):
        return None

    if user_msg is None:
        user_msg = await message.get_reply_message()

    # todo improve this uploading ✔️
    file_name = os.path.basename(path)
    caption_str = ""
    caption_str += "<code>"
    caption_str += file_name
    caption_str += "</code>"
    metadata = extractMetadata(createParser(path))

    if metadata is not None:
        # handle none for unknown
        metadata = metadata.exportDictionary()
        try:
            mime = metadata.get("Common").get("MIME type")
        except:
            mime = metadata.get("Metadata").get("MIME type")

        ftype = mime.split("/")[0]
        ftype = ftype.lower().strip()
    else:
        ftype = "unknown"
    # print(metadata)

    if not force_edit:
        data = "upcancel {} {} {}".format(
            message.chat_id, message.id, user_msg.sender_id
        )
        buts = [KeyboardButtonCallback("Cancel upload.", data.encode("UTF-8"))]
        msg = await message.reply("**Uploading:** `{}`".format(file_name), buttons=buts)

    else:
        msg = message

    uploader_id = None
    if queue is not None:
        torlog.info(f"Waiting for the worker here for {file_name}")
        msg = await msg.edit(f"{msg.text}\nWaiting for a uploaders to get free... ")
        uploader_id = await queue.get()
        torlog.info(
            f"Waiting over for the worker here for {file_name} aquired worker {uploader_id}"
        )

    out_msg = None
    start_time = time.time()
    tout = get_val("EDIT_SLEEP_SECS")
    opath = path

    if user_msg is not None:
        dis_thumb = user_db.get_var("DISABLE_THUMBNAIL", user_msg.sender_id)
        if dis_thumb is False or dis_thumb is None:
            thumb_path = user_db.get_thumbnail(user_msg.sender_id)
            if not thumb_path:
                thumb_path = None

    try:
        if get_val("FAST_UPLOAD"):
            torlog.info("Fast upload is enabled")
            with open(path, "rb") as filee:
                path = await upload_file(
                    message.client,
                    filee,
                    file_name,
                    lambda c, t: progress(
                        c, t, msg, file_name, start_time, tout, message, database
                    ),
                )

        if user_msg is not None:
            force_docs = user_db.get_var("FORCE_DOCUMENTS", user_msg.sender_id)
        else:
            force_docs = None

        if force_docs is None:
            force_docs = get_val("FORCE_DOCUMENTS")

        if message.media and force_edit:
            out_msg = await msg.edit(file=path, text=caption_str)
        else:

            if ftype == "video" and not force_docs:
                try:
                    if thumb_path is not None:
                        thumb = thumb_path
                    else:
                        thumb = await thumb_manage.get_thumbnail(opath)
                except:
                    thumb = None
                    torlog.exception("Error in thumb")
                try:
                    attrs, _ = get_attributes(opath, supports_streaming=True)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        thumb=thumb,
                        caption=caption_str,
                        reply_to=message.id,
                        supports_streaming=True,
                        progress_callback=lambda c, t: progress(
                            c, t, msg, file_name, start_time, tout, message, database
                        ),
                        attributes=attrs,
                    )
                except VideoContentTypeInvalidError:
                    attrs, _ = get_attributes(opath, force_document=True)
                    torlog.warning("Streamable file send failed fallback to document.")
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        caption=caption_str,
                        thumb=thumb,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c, t: progress(
                            c, t, msg, file_name, start_time, tout, message, database
                        ),
                        attributes=attrs,
                    )
                except Exception:
                    torlog.error("Error:- {}".format(traceback.format_exc()))
            elif ftype == "audio" and not force_docs:
                # not sure about this if
                attrs, _ = get_attributes(opath)
                out_msg = await msg.client.send_file(
                    msg.to_id,
                    file=path,
                    parse_mode="html",
                    caption=caption_str,
                    reply_to=message.id,
                    progress_callback=lambda c, t: progress(
                        c, t, msg, file_name, start_time, tout, message, database
                    ),
                    attributes=attrs,
                )
            else:
                if force_docs:
                    attrs, _ = get_attributes(opath, force_document=True)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        caption=caption_str,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c, t: progress(
                            c, t, msg, file_name, start_time, tout, message, database
                        ),
                        attributes=attrs,
                        thumb=thumb_path,
                    )
                else:
                    attrs, _ = get_attributes(opath)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        caption=caption_str,
                        reply_to=message.id,
                        progress_callback=lambda c, t: progress(
                            c, t, msg, file_name, start_time, tout, message, database
                        ),
                        attributes=attrs,
                        thumb=thumb_path,
                    )
    except Exception as e:
        if str(e).find("cancel") != -1:
            torlog.info("Canceled an upload lol")
            await msg.edit(f"Failed to upload {e}", buttons=None)
        else:
            torlog.exception("In Tele Upload")
            await msg.edit(f"Failed to upload {e}", buttons=None)
    finally:
        if queue is not None:
            await queue.put(uploader_id)
            torlog.info(f"Freed uploader with id {uploader_id}")

    if out_msg is None:
        return None
    if out_msg.id != msg.id:
        await msg.delete()

    return out_msg


def black_list_exts(file):
    for i in ["!qb"]:
        if str(file).lower().endswith(i):
            return True

    return False


# async def upload_single_file(message, local_file_name, caption_str, from_user, edit_media):
async def upload_single_file(
    path, message, force_edit, database=None, thumb_image_path=None, user_msg=None
):
    if database is not None:
        if database.get_cancel_status(message.chat_id, message.id):
            # add os remove here
            return None
    if not os.path.exists(path):
        return None

    queue = message.client.exqueue

    file_name = os.path.basename(path)
    caption_str = ""
    caption_str += "<code>"
    caption_str += file_name
    caption_str += "</code>"

    if user_msg is None:
        user_msg = await message.get_reply_message()

    if user_msg is not None:
        force_docs = user_db.get_var("FORCE_DOCUMENTS", user_msg.sender_id)
    else:
        force_docs = None

    if force_docs is None:
        force_docs = get_val("FORCE_DOCUMENTS")

    # Avoid Flood in Express
    await asyncio.sleep(15)

    metadata = extractMetadata(createParser(path))

    if metadata is not None:
        # handle none for unknown
        metadata = metadata.exportDictionary()
        try:
            mime = metadata.get("Common").get("MIME type")
        except:
            mime = metadata.get("Metadata").get("MIME type")

        ftype = mime.split("/")[0]
        ftype = ftype.lower().strip()
    else:
        ftype = "unknown"

    thonmsg = message
    message = await message.client.pyro.get_messages(message.chat_id, message.id)
    tout = get_val("EDIT_SLEEP_SECS")
    sent_message = None
    start_time = time.time()
    #
    if user_msg is not None:
        dis_thumb = user_db.get_var("DISABLE_THUMBNAIL", user_msg.sender_id)
        if dis_thumb is False or dis_thumb is None:
            thumb_image_path = user_db.get_thumbnail(user_msg.sender_id)
            if not thumb_image_path:
                thumb_image_path = None
    #
    uploader_id = None
    try:
        message_for_progress_display = message
        if not force_edit:
            data = "upcancel {} {} {}".format(
                message.chat.id, message.message_id, user_msg.sender_id
            )
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Cancel Upload", callback_data=data.encode("UTF-8")
                        )
                    ]
                ]
            )
            message_for_progress_display = await message.reply_text(
                "**Starting upload of** `{}`".format(os.path.basename(path)),
                reply_markup=markup,
            )

            if queue is not None:
                torlog.info(f"Waiting for the worker here for {file_name}")
                message_for_progress_display = await message_for_progress_display.edit(
                    f"{message_for_progress_display.text}\nWaiting for a uploaders to get free... "
                )
                uploader_id = await queue.get()
                torlog.info(
                    f"Waiting over for the worker here for {file_name} aquired worker {uploader_id}"
                )

        if ftype == "video" and not force_docs:
            metadata = extractMetadata(createParser(path))
            duration = 0
            if metadata.has("duration"):
                duration = metadata.get("duration").seconds
            #
            width = 1280
            height = 720
            if thumb_image_path is None:
                thumb_image_path = await thumb_manage.get_thumbnail(path)
                # get the correct width, height, and duration for videos greater than 10MB

            thumb = None
            if thumb_image_path is not None and os.path.isfile(thumb_image_path):
                thumb = thumb_image_path

            # send video
            if force_edit and message.photo:
                sent_message = await message.edit_media(
                    media=InputMediaVideo(
                        media=path,
                        thumb=thumb,
                        parse_mode="html",
                        width=width,
                        height=height,
                        duration=duration,
                        supports_streaming=True,
                        caption=caption_str,
                    )
                    # quote=True,
                )
            else:
                sent_message = await message.reply_video(
                    video=path,
                    # quote=True,
                    parse_mode="html",
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    caption=caption_str,
                    supports_streaming=True,
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        f"{os.path.basename(path)}",
                        message_for_progress_display,
                        start_time,
                        tout,
                        thonmsg.client.pyro,
                        message,
                        database,
                        markup,
                    ),
                )
            if thumb is not None:
                os.remove(thumb)
        elif ftype == "audio" and not force_docs:
            metadata = extractMetadata(createParser(path))
            duration = 0
            title = ""
            artist = ""
            if metadata.has("duration"):
                duration = metadata.get("duration").seconds
            if metadata.has("title"):
                title = metadata.get("title")
            if metadata.has("artist"):
                artist = metadata.get("artist")

            thumb = None
            if thumb_image_path is not None and os.path.isfile(thumb_image_path):
                thumb = thumb_image_path
            # send audio
            if force_edit and message.photo:
                sent_message = await message.edit_media(
                    media=InputMediaAudio(
                        media=path,
                        thumb=thumb,
                        parse_mode="html",
                        duration=duration,
                        performer=artist,
                        title=title,
                        caption=caption_str,
                    )
                    # quote=True,
                )
            else:
                sent_message = await message.reply_audio(
                    audio=path,
                    # quote=True,
                    parse_mode="html",
                    duration=duration,
                    performer=artist,
                    title=title,
                    caption=caption_str,
                    thumb=thumb,
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        f"{os.path.basename(path)}",
                        message_for_progress_display,
                        start_time,
                        tout,
                        thonmsg.client.pyro,
                        message,
                        database,
                        markup,
                    ),
                )
            if thumb is not None:
                os.remove(thumb)
        else:
            # if a file, don't upload "thumb"
            # this "diff" is a major derp -_- 😔😭😭
            thumb = None
            if thumb_image_path is not None and os.path.isfile(thumb_image_path):
                thumb = thumb_image_path
            #
            # send document
            if force_edit and message.photo:
                sent_message = await message.edit_media(
                    media=InputMediaDocument(
                        media=path, caption=caption_str, thumb=thumb, parse_mode="html"
                    )
                    # quote=True,
                )
            else:
                sent_message = await message.reply_document(
                    document=path,
                    # quote=True,
                    thumb=thumb,
                    parse_mode="html",
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    caption=caption_str,
                    progress_args=(
                        f"{os.path.basename(path)}",
                        message_for_progress_display,
                        start_time,
                        tout,
                        thonmsg.client.pyro,
                        message,
                        database,
                        markup,
                    ),
                )
            if thumb is not None:
                os.remove(thumb)
    except Exception as e:
        if str(e).find("cancel") != -1:
            torlog.info("Canceled an upload lol")
            try:
                await message_for_progress_display.edit(f"Failed to upload {e}")
            except:
                pass
        else:
            try:
                await message_for_progress_display.edit(f"Failed to upload {e}")
            except:
                pass
            torlog.exception("IN Pyro upload")
    else:
        if message.message_id != message_for_progress_display.message_id:
            await message_for_progress_display.delete()
    finally:
        if queue is not None and uploader_id is not None:
            await queue.put(uploader_id)
            torlog.info(f"Freed uploader with id {uploader_id}")
    # os.remove(path)
    if sent_message is None:
        return None
    sent_message = await thonmsg.client.get_messages(
        sent_message.chat.id, ids=sent_message.message_id
    )
    return sent_message
