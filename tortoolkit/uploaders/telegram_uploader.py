import asyncio
from functools import partial

from pyrogram.types import InputMediaDocument, InputMediaVideo, InputMediaPhoto, InputMediaAudio, InlineKeyboardButton, InlineKeyboardMarkup
from ..core.base_task import BaseTask
from ..core.database_handle import TtkUpload
from ..database.dbhandler import UserDB
import os
import logging
from telethon.tl.types import KeyboardButtonCallback
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from ..core.getVars import get_val
import shutil
from .Ftele import upload_file
from ..utils import video_helpers, zip7_utils
from ..utils.progress_for_telethon import progress
from ..utils.progress_for_pyrogram import progress_for_pyrogram
import time
from telethon.utils import get_attributes
from telethon.errors import VideoContentTypeInvalidError

torlog = logging.getLogger(__name__)

class TelegramUploader(BaseTask):
    class TelegramStatus:
        def __init__(self, files, uploaded_files=0, current_file="") -> None:
            self.files = files
            self.uploaded_files = uploaded_files
            self.current_file = current_file
            


    def __init__(self, path, user_message, previous_task_msg=None, pyroclient = None):
        super().__init__()

        self._current_update = None
        self._path = path
        self._user_message = user_message
        self._client = user_message.client
        self._previous_task_msg = previous_task_msg
        self._pyro_client = pyroclient
        self._updb = TtkUpload()
        self.files_dict = {}
        self._user_db = UserDB()
        

    async def execute(self):
        self._update_message = await self._user_message.reply("Uploading files...")
        self._total_files = self.get_num_of_files(self._path)
        self._num_files = 0
        self._up_file_name = ""
        self._current_update = TelegramUploader.TelegramStatus(self._total_files)
        await self.upload_handel(self._update_message)

        return self.files_dict


    async def upload_handel(self, message, path=None,from_in=False):
        # creting here so connections are kept low
        if self._updb is None:
            # Central object is not used its Acknowledged 
            self._updb = TtkUpload()
        
        if path is None:
            path = self._path

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

            try:
                message = await message.edit("{}\nFound **{}** files for this download.".format(message.text,len(directory_contents)))
            except:
                torlog.warning("Too much folders will stop the editing of this message")
            
            if not from_in:
                self._updb.register_upload(message.chat_id,message.id)
                if self._user_message is None:
                    sup_mes = await message.get_reply_message()
                else:
                    sup_mes = self._user_message
                
                data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
                buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
                message = await message.edit(buttons=buts)


            for file in directory_contents:
                if self._updb.get_cancel_status(message.chat_id,message.id):
                    continue

                await self.upload_handel(
                    message,
                    os.path.join(path,file),
                    from_in=True
                )
            
            if not from_in:
                if self._updb.get_cancel_status(message.chat_id,message.id):
                    self._is_canceled = True
                    self._is_done = True
                    self._error_reason = "{} - Canceled By user.".format(message.text)
                    await message.edit("{} - Canceled By user.".format(message.text),buttons=None)
                else:
                    await message.edit(buttons=None)
                self._updb.deregister_upload(message.chat_id,message.id)

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
                    todel = await message.reply("**FILE LAGRE THEN THRESHOLD, SPLITTING NOW...**\n`Using Algo FFMPEG VIDEO SPLIT`") 
                    split_dir = await video_helpers.split_file(path,get_val("TG_UP_LIMIT"))
                    await todel.delete()
                else:
                    todel = await message.reply("**FILE LAGRE THEN THRESHOLD, SPLITTING NOW...**\n`Using Algo FFMPEG ZIP SPLIT`") 
                    split_dir = await zip7_utils.split_in_zip(path,get_val("TG_UP_LIMIT"))
                    await todel.delete()
                
                dircon = os.listdir(split_dir)
                dircon.sort()

                if not from_in:
                    self._updb.register_upload(message.chat_id,message.id)
                    if self._user_message is None:
                        sup_mes = await message.get_reply_message()
                    else:
                        sup_mes = self._user_message

                    data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
                    buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
                    await message.edit(buttons=buts)

                for file in dircon:
                    if self._updb.get_cancel_status(message.chat_id,message.id):
                        continue
                
                    await self.upload_handel(
                        message,
                        os.path.join(split_dir,file),
                        from_in=True
                    )
                
                try:
                    shutil.rmtree(split_dir)
                    os.remove(path)
                except:pass
                
                if not from_in:
                    if self._updb.get_cancel_status(message.chat_id,message.id):
                        self._is_canceled = True
                        self._is_done = True
                        self._error_reason = "{} - Canceled By user.".format(message.text)
                        await message.edit("{} - Canceled By user.".format(message.text),buttons=None)
                    else:
                        await message.edit(buttons=None)
                    self._updb.deregister_upload(message.chat_id,message.id)
                # spliting file logic blah blah
            else:
                if not from_in:
                    self._updb.register_upload(message.chat_id,message.id)
                    if self._user_message is None:
                        sup_mes = await message.get_reply_message()
                    else:
                        sup_mes = self._user_message

                    data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
                    buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
                    await message.edit(buttons=buts)
                #print(updb)
                if black_list_exts(path):
                    self._num_files += 1
                    self._up_file_name =os.path.basename(path)
                    sentmsg = None
                else:
                    sentmsg = await self.upload_a_file(path,message)

                if not from_in:
                    if self._updb.get_cancel_status(message.chat_id,message.id):
                        self._is_canceled = True
                        self._is_done = True
                        self._error_reason = "{} - Canceled By user.".format(message.text)

                        await message.edit("{} - Canceled By user.".format(message.text),buttons=None)
                    else:
                        await message.edit(buttons=None)
                    self._updb.deregister_upload(message.chat_id,message.id)

                if sentmsg is not None:
                    self._up_file_name = os.path.basename(path)
                    self._num_files += 1
                    self.files_dict[os.path.basename(path)] = sentmsg.id

    async def upload_a_file(self, path, message):
        if get_val("EXPRESS_UPLOAD"):
            return await self.upload_single_file(path, message)
        
        queue = self._client.queue
        if self._updb is not None:
            if self._updb.get_cancel_status(message.chat_id,message.id):
                # add os remove here
                return None
        if not os.path.exists(path):
            return None
            
        if self._user_message is None:
            self._user_message = await message.get_reply_message()
        
        #todo improve this uploading ✔️
        file_name = os.path.basename(path)
        caption_str = ""
        caption_str += "<code>"
        caption_str += file_name
        caption_str += "</code>"
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
        

              
        data = "upcancel {} {} {}".format(message.chat_id,message.id,self._user_message.sender_id)
        buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
        msg = await message.reply("**Uploading:** `{}`".format(file_name),buttons=buts)

        uploader_id = None
        if queue is not None:
            torlog.info(f"Waiting for the worker here for {file_name}")
            msg = await msg.edit(f"{msg.text}\nWaiting for a uploaders to get free... ")
            uploader_id = await queue.get()
            torlog.info(f"Waiting over for the worker here for {file_name} aquired worker {uploader_id}")

        out_msg = None
        start_time = time.time()
        tout = get_val("EDIT_SLEEP_SECS")
        opath = path
        
        if self._user_message is not None:
            dis_thumb = self._user_db.get_variable("DISABLE_THUMBNAIL", self._user_message.sender_id)
            if dis_thumb is False or dis_thumb is None:
                thumb_path = self._user_db.get_thumbnail(self._user_message.sender_id)
                if not thumb_path:
                    thumb_path = None
        
        try:
            if get_val("FAST_UPLOAD"):
                torlog.info("Fast upload is enabled")
                with open(path,"rb") as filee:
                    path = await upload_file(message.client,filee,file_name,
                    lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,self._updb)
                    )

            if self._user_message is not None:
                force_docs = self._user_db.get_variable("FORCE_DOCUMENTS",self._user_message.sender_id)  
            else:
                force_docs = None
            
            if force_docs is None:
                force_docs = get_val("FORCE_DOCUMENTS")
            
            if ftype == "video" and not force_docs:
                try:
                    if thumb_path is not None:
                        thumb = thumb_path
                    else:
                        thumb = await video_helpers.get_thumbnail(opath)
                except:
                    thumb = None
                    torlog.exception("Error in thumb")
                try:
                    attrs, _ = get_attributes(opath,supports_streaming=True)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        thumb=thumb,
                        caption=caption_str,
                        reply_to=message.id,
                        supports_streaming=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,self._updb),
                        attributes=attrs
                    )
                except VideoContentTypeInvalidError:
                    attrs, _ = get_attributes(opath,force_document=True)
                    torlog.warning("Streamable file send failed fallback to document.")
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        caption=caption_str,
                        thumb=thumb,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,self._updb),
                        attributes=attrs
                    )
                except Exception:
                    torlog.exception("Error:- in Upload")
            elif ftype == "audio" and not force_docs:
                # not sure about this if
                attrs, _ = get_attributes(opath)
                out_msg = await msg.client.send_file(
                    msg.to_id,
                    file=path,
                    parse_mode="html",
                    caption=caption_str,
                    reply_to=message.id,
                    progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,self._updb),
                    attributes=attrs
                )
            else:
                if force_docs:
                    attrs, _ = get_attributes(opath,force_document=True)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        caption=caption_str,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,self._updb),
                        attributes=attrs,
                        thumb=thumb_path
                    )
                else:
                    attrs, _ = get_attributes(opath)
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        parse_mode="html",
                        caption=caption_str,
                        reply_to=message.id,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,self._updb),
                        attributes=attrs,
                        thumb=thumb_path
                    )
        except Exception as e:
            if str(e).find("cancel") != -1:
                torlog.info("Canceled an upload lol")
                await msg.edit(f"Failed to upload {e}", buttons=None)
            else:
                torlog.exception("In Tele Upload")
                await msg.edit(f"Failed to upload {e}",  buttons=None)
        finally:
            if queue is not None:
                await queue.put(uploader_id)
                torlog.info(f"Freed uploader with id {uploader_id}")
                    

        if out_msg is None:
            return None
        if out_msg.id != msg.id:
            await msg.delete()
        
        return out_msg

    async def upload_single_file(self, path, message):
        if self._updb is not None:
            if self._updb.get_cancel_status(message.chat_id,message.id):
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

        if self._user_message is None:
            self._user_message = await message.get_reply_message()

        if self._user_message is not None:
            force_docs = self._user_db.get_variable("FORCE_DOCUMENTS",self._user_message.sender_id)  
        else:
            force_docs = None
            
        if force_docs is None:
            force_docs = get_val("FORCE_DOCUMENTS")
        
        # Avoid Flood in Express
        await asyncio.sleep(5)

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
        if self._user_message is not None:
            dis_thumb = self._user_db.get_variable("DISABLE_THUMBNAIL", self._user_message.sender_id)
            if dis_thumb is False or dis_thumb is None:
                thumb_image_path = self._user_db.get_thumbnail(self._user_message.sender_id)
                if not thumb_image_path:
                    thumb_image_path = None
        #
        uploader_id = None
        try:
            message_for_progress_display = message
            
            data = "upcancel {} {} {}".format(message.chat.id,message.message_id,self._user_message.sender_id)
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cancel Upload", callback_data=data.encode("UTF-8"))]])
            message_for_progress_display = await message.reply_text(
                "**Starting upload of** `{}`".format(os.path.basename(path)),
                reply_markup=markup
            )
             
            if queue is not None:
                torlog.info(f"Waiting for the worker here for {file_name}")
                message_for_progress_display = await message_for_progress_display.edit(f"{message_for_progress_display.text}\nWaiting for a uploaders to get free... ")
                uploader_id = await queue.get()
                torlog.info(f"Waiting over for the worker here for {file_name} aquired worker {uploader_id}")
            
            if ftype == "video" and not force_docs:
                metadata = extractMetadata(createParser(path))
                duration = 0
                if metadata.has("duration"):
                    duration = metadata.get('duration').seconds
                #
                width = 1280
                height = 720
                if thumb_image_path is None:
                    thumb_image_path = await video_helpers.get_thumbnail(path)
                    # get the correct width, height, and duration for videos greater than 10MB

                thumb = None
                if thumb_image_path is not None and os.path.isfile(thumb_image_path):
                    thumb = thumb_image_path
                
                # send video
                
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
                        self._updb,
                        markup
                    )
                )
                if thumb is not None:
                    os.remove(thumb)
            elif ftype == "audio" and not force_docs:
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
                        self._updb,
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
                        self._updb,
                        markup
                    )
                )
                if thumb is not None:
                    os.remove(thumb)
        except Exception as e:
            if str(e).find("cancel") != -1:
                torlog.info("Canceled an upload lol")
                try:
                    await message_for_progress_display.edit(f"Failed to upload {e}")
                except:pass
            else:
                try:
                    await message_for_progress_display.edit(f"Failed to upload {e}")
                except:pass
                torlog.exception("IN Pyro upload")
        else:
            if message.message_id != message_for_progress_display.message_id:
                await message_for_progress_display.delete()
        finally:
            if queue is not None and uploader_id is not None:
                await queue.put(uploader_id)
                torlog.info(f"Freed uploader with id {uploader_id}")
        #os.remove(path)
        if sent_message is None:
            return None
        sent_message = await thonmsg.client.get_messages(sent_message.chat.id, ids=sent_message.message_id)
        return sent_message

    def re_calc_files(self):
        self._total_files = self.get_num_of_files(self._path)

    def get_num_of_files(self, path):
        num = 0
        for file in os.listdir(path):
            if os.path.isdir(os.path.join(path,file)):
                num += self.get_num_of_files(os.path.join(path,file))
            else:
                num += 1
        return num
    
    def cancel(self, is_admin=False):
        self._is_canceled = True
        if is_admin:
            self._canceled_by = self.ADMIN
        else: 
            self._canceled_by = self.USER
    
    async def get_update(self):
        self._current_update = TelegramUploader.TelegramStatus(self._total_files, self._num_files, self._up_file_name)
        return self._current_update

    def get_error_reason(self):
        return self._error_reason

def black_list_exts(file):
    for i in ['!qb']:
        if str(file).lower().endswith(i):
            return True
    
    return False