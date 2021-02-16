# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import os,logging,time,traceback,shutil
from ..core.getVars import get_val
from ..core import thumb_manage # i guess i will dodge this one ;) as i am importing the vids helper anyways
from . import vids_helpers,zip7_utils
from .progress_for_telethon import progress
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from telethon.errors import VideoContentTypeInvalidError
from ..core.database_handle import TtkUpload
from .. import user_db
from telethon.tl.types import KeyboardButtonCallback,DocumentAttributeVideo,DocumentAttributeAudio
from telethon.utils import get_attributes
from .Ftele import upload_file
from pyrogram.types import InputMediaDocument, InputMediaVideo, InputMediaPhoto, InputMediaAudio, InlineKeyboardButton, InlineKeyboardMarkup
from .progress_for_pyrogram import progress_for_pyrogram
torlog = logging.getLogger(__name__)

#thanks @SpEcHiDe for this concept of recursion
async def upload_handel(path,message,from_uid,files_dict,job_id=0,force_edit=False,updb=None,from_in=False,thumb_path=None, user_msg=None):
    # creting here so connections are kept low
    if updb is None:
        # Central object is not used its Acknowledged 
        updb = TtkUpload()

    #logging.info("Uploading Now:- {}".format(path))

    if os.path.isdir(path):
        logging.info("Uplaoding the directory:- {}".format(path))

        directory_contents = os.listdir(path)
        directory_contents.sort()
        try:
            # maybe way to refresh?!
            message = await message.client.get_messages(message.chat_id,ids=[message.id])
            message = message[0]
        except:pass

        message = await message.edit("{}\nFound {} files for this download".format(message.text,len(directory_contents)))
        
        if not from_in:
            updb.register_upload(message.chat_id,message.id)
            if user_msg is None:
                sup_mes = await message.get_reply_message()
            else:
                sup_mes = user_msg
            
            data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
            buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
            message = await message.edit(buttons=buts)


        for file in directory_contents:
            if updb.get_cancel_status(message.chat_id,message.id):
                continue

            await upload_handel(
                os.path.join(path,file),
                message,
                from_uid,
                files_dict,
                job_id,
                force_edit,
                updb,
                from_in=True,
                thumb_path=thumb_path,
                user_msg=user_msg
            )
        
        if not from_in:
            if updb.get_cancel_status(message.chat_id,message.id):
                await message.edit("{} - Cancled By user.".format(message.text),buttons=None)
            else:
                await message.edit(buttons=None)
            updb.deregister_upload(message.chat_id,message.id)

    else:
        logging.info("Uplaoding the file:- {}".format(path))
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
                todel = await message.reply("FILE LAGRE THEN THRESHOLD SPLITTING NOW.Processing.....\n```Using Algo FFMPEG SPLIT```") 
                split_dir = await vids_helpers.split_file(path,get_val("TG_UP_LIMIT"))
            else:
                todel = await message.reply("FILE LAGRE THEN THRESHOLD SPLITTING NOW.Processing.....\n```Using Algo PARTED ZIP SPLIT```") 
                split_dir = await zip7_utils.split_in_zip(path,get_val("TG_UP_LIMIT"))
            
            dircon = os.listdir(split_dir)
            dircon.sort()

            if not from_in:
                updb.register_upload(message.chat_id,message.id)
                if user_msg is None:
                    sup_mes = await message.get_reply_message()
                else:
                    sup_mes = user_msg
                data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
                buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
                await message.edit(buttons=buts)

            for file in dircon:
                if updb.get_cancel_status(message.chat_id,message.id):
                    continue
            
                await upload_handel(
                    os.path.join(split_dir,file),
                    message,
                    from_uid,
                    files_dict,
                    job_id,
                    force_edit,
                    updb=updb,
                    from_in=True,
                    thumb_path=thumb_path,
                    user_msg=user_msg
                )
            
            try:
                shutil.rmtree(split_dir)
                os.remove(path)
            except:pass
            
            if not from_in:
                if updb.get_cancel_status(message.chat_id,message.id):
                    await message.edit("{} - Cancled By user.".format(message.text),buttons=None)
                else:
                    await message.edit(buttons=None)
                updb.deregister_upload(message.chat_id,message.id)
            # spliting file logic blah blah
        else:
            if not from_in:
                updb.register_upload(message.chat_id,message.id)
                if user_msg is None:
                    sup_mes = await message.get_reply_message()
                else:
                    sup_mes = user_msg
                
                data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
                buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
                await message.edit(buttons=buts)
            #print(updb)
            if black_list_exts(path):
                sentmsg = None
            else:
                sentmsg = await upload_a_file(
                    path,
                    message,
                    force_edit,
                    updb,
                    thumb_path,
                    user_msg=user_msg
                )

            if not from_in:
                if updb.get_cancel_status(message.chat_id,message.id):
                    await message.edit("{} - Cancled By user.".format(message.text),buttons=None)
                else:
                    await message.edit(buttons=None)
                updb.deregister_upload(message.chat_id,message.id)

            if sentmsg is not None:
                files_dict[os.path.basename(path)] = sentmsg.id

    return files_dict



async def upload_a_file(path,message,force_edit,database=None,thumb_path=None,user_msg=None):
    if get_val("EXPRESS_UPLOAD"):
        return await upload_single_file(path, message, force_edit, database, thumb_path, user_msg)
    queue = message.client.queue
    if database is not None:
        if database.get_cancel_status(message.chat_id,message.id):
            # add os remove here
            return None
    if not os.path.exists(path):
        return None
        
    
    #todo improve this uploading ✔️
    file_name = os.path.basename(path)
    metadata = extractMetadata(createParser(path))
    ometa = metadata
    
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
    #print(metadata)
    

    if not force_edit:
        if user_msg is None:
            sup_mes = await message.get_reply_message()
        else:
            sup_mes = user_msg
        
        data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
        buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
        msg = await message.reply("Uploading {}".format(file_name),buttons=buts)
    else:
        msg = message

    uploader_id = None
    if queue is not None:
        torlog.info(f"Waiting for the worker here for {file_name}")
        msg = await msg.edit(f"{msg.text} - Waiting for a uploaders to get free")
        uploader_id = await queue.get()
        torlog.info(f"Waiting over for the worker here for {file_name} aquired worker {uploader_id}")

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
            with open(path,"rb") as filee:
                path = await upload_file(message.client,filee,file_name,
                lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
                )


    
        if message.media and force_edit:
            out_msg = await msg.edit(
                file=path,
                text=file_name
            )
        else:
            
            if ftype == "video":
                if user_msg is not None:
                    force_docs = user_db.get_var("FORCE_DOCUMENTS",user_msg.sender_id)  
                else:
                    force_docs = None

                
                if force_docs is None:
                    force_docs = get_val("FORCE_DOCUMENTS") 
                if force_docs == True:
                    attrs, _ = get_attributes(opath,force_document=True)
                    # add the thumbs for the docs too
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        caption=file_name,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database),
                        attributes=attrs,
                        thumb=thumb_path
                    )
                else:
                    try:
                        if thumb_path is not None:
                            thumb = thumb_path
                        else:
                            thumb = await thumb_manage.get_thumbnail(opath)
                    except:
                        thumb = None
                        torlog.exception("Error in thumb")
                    try:
                        attrs, _ = get_attributes(opath,supports_streaming=True)
                        out_msg = await msg.client.send_file(
                            msg.to_id,
                            file=path,
                            thumb=thumb,
                            caption=file_name,
                            reply_to=message.id,
                            supports_streaming=True,
                            progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database),
                            attributes=attrs
                        )
                    except VideoContentTypeInvalidError:
                        attrs, _ = get_attributes(opath,force_document=True)
                        torlog.warning("Streamable file send failed fallback to document.")
                        out_msg = await msg.client.send_file(
                            msg.to_id,
                            file=path,
                            caption=file_name,
                            thumb=thumb,
                            reply_to=message.id,
                            force_document=True,
                            progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database),
                            attributes=attrs
                        )
                    except Exception:
                        torlog.error("Error:- {}".format(traceback.format_exc()))
            elif ftype == "audio":
                # not sure about this if
                attrs, _ = get_attributes(opath)
                out_msg = await msg.client.send_file(
                    msg.to_id,
                    file=path,
                    caption=file_name,
                    reply_to=message.id,
                    progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database),
                    attributes=attrs
                )
            else:
                if user_msg is not None:
                    force_docs = user_db.get_var("FORCE_DOCUMENTS",user_msg.sender_id)  
                else:
                    force_docs = None
                
                if force_docs is None:
                    force_docs = get_val("FORCE_DOCUMENTS") 
                if force_docs:
                    attrs, _ = get_attributes(opath,force_document=True)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        caption=file_name,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database),
                        attributes=attrs,
                        thumb=thumb_path
                    )
                else:
                    attrs, _ = get_attributes(opath)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        caption=file_name,
                        reply_to=message.id,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database),
                        attributes=attrs
                    )
    except Exception as e:
        if str(e).find("cancel") != -1:
            torlog.info("cancled an upload lol")
            await msg.delete()
        else:
            torlog.info(traceback.format_exc())
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
    for i in ['!qb']:
        if str(file).lower().endswith(i):
            return True
    
    return False

#async def upload_single_file(message, local_file_name, caption_str, from_user, edit_media):
async def upload_single_file(path, message, force_edit,database=None,thumb_image_path=None,user_msg=None):
    if database is not None:
        if database.get_cancel_status(message.chat_id,message.id):
            # add os remove here
            return None
    if not os.path.exists(path):
        return None
    
    force_docs = get_val("FORCE_DOCUMENTS")
    if user_msg is not None:
        force_docs = user_db.get_var("FORCE_DOCUMENTS",user_msg.sender_id)

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
    try:
        message_for_progress_display = message
        if not force_edit:
            data = "upcancel {} {} {}".format(message.chat.id,message.message_id,user_msg.sender_id)
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cancel Upload", callback_data=data.encode("UTF-8"))]])
            message_for_progress_display = await message.reply_text(
                "starting upload of {}".format(os.path.basename(path)),
                reply_markup=markup
            )
        if str(path).upper().endswith(("MKV", "MP4", "WEBM")) and not force_docs:
            metadata = extractMetadata(createParser(path))
            duration = 0
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
            #
            width = 0
            height = 0
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
                        supports_streaming=True
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
                    supports_streaming=True,
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "trying to upload",
                        message_for_progress_display,
                        start_time,
                        tout,
                        thonmsg.client.pyro,
                        message,
                        database,
                        markup
                    )
                )
            if thumb is not None:
                os.remove(thumb)
        elif str(path).upper().endswith(("MP3", "M4A", "M4B", "FLAC", "WAV")) and not force_docs:
            metadata = extractMetadata(createParser(path))
            duration = 0
            title = ""
            artist = ""
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
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
                        title=title
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
                    thumb=thumb,
                    disable_notification=True,
                    # reply_to_message_id=message.reply_to_message.message_id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        "trying to upload",
                        message_for_progress_display,
                        start_time,
                        tout,
                        thonmsg.client.pyro,
                        message,
                        database,
                        markup
                    )
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
                        media=path,
                        thumb=thumb,
                        parse_mode="html"
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
                    progress_args=(
                        "trying to upload",
                        message_for_progress_display,
                        start_time,
                        tout,
                        thonmsg.client.pyro,
                        message,
                        database,
                        markup
                    )
                )
            if thumb is not None:
                os.remove(thumb)
    except Exception as e:
        if str(e).find("cancel") != -1:
            torlog.info("cancled an upload lol")
            await message_for_progress_display.delete()
        else:
            torlog.info(traceback.format_exc())
    else:
        if message.message_id != message_for_progress_display.message_id:
            await message_for_progress_display.delete()
    #os.remove(path)
    if sent_message is None:
        return None
    sent_message = await thonmsg.client.get_messages(sent_message.chat.id, ids=sent_message.message_id)
    return sent_message
