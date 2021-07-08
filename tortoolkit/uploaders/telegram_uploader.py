from tortoolkit.tortoolkit.database.abstract_db import TorLog
from ..core.base_task import BaseTask
from ..core.database_handle import TtkUpload
import os
import logging

torlog = logging.getLogger(__name__)

class TelegramUploader(BaseTask):
    class TelegramStatus:
        def __init__(self, files, uploaded_files=0, current_file="") -> None:
            self.files = files
            self.uploaded_files = uploaded_files
            self.current_file = current_file


    def __init__(self, path, user_message, previous_task_msg=None, client = None):
        super().__init__()

        self._currnet_update = None
        self._path = path
        self._user_message = user_message
        self._previous_task_msg = previous_task_msg
        self._updb = TtkUpload()

        if client is None:
            self._client = user_message.client
        else:
            self._client = client

    async def execute(self, path=None):
        if path is None:
            path = self._path
        
        if self._updb is None:
            # Central object is not used its Acknowledged 
            self._updb = TtkUpload()

        #logging.info("Uploading Now:- {}".format(path))

        if os.path.isdir(path):
            torlog.info("Uplaoding the directory:- {}".format(path))

            directory_contents = os.listdir(path)
            directory_contents.sort()
            try:
                # maybe way to refresh?!
                message = await self._client.get_messages(self.message.chat_id,ids=[message.id])
                message = message[0]
            except:pass

            try:
                message = await message.edit("{}\nFound **{}** files for this download.".format(message.text,len(directory_contents)))
            except:
                torlog.warning("Too much folders will stop the editing of this message")
            
            if not from_in:
                updb.register_upload(message.chat_id,message.id)
                if user_msg is None:
                    sup_mes = await message.get_reply_message()
                else:
                    sup_mes = user_msg
                
                if task is not None:
                    await task.set_message(message)
                    await task.set_original_message(sup_mes)
                
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
                    user_msg=user_msg,
                    task=task
                )
            
            if not from_in:
                if updb.get_cancel_status(message.chat_id,message.id):
                    task.cancel = True
                    await task.set_inactive()
                    await message.edit("{} - Canceled By user.".format(message.text),buttons=None)
                else:
                    await message.edit(buttons=None)
                updb.deregister_upload(message.chat_id,message.id)

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
                    split_dir = await vids_helpers.split_file(path,get_val("TG_UP_LIMIT"))
                    await todel.delete()
                else:
                    todel = await message.reply("**FILE LAGRE THEN THRESHOLD, SPLITTING NOW...**\n`Using Algo FFMPEG ZIP SPLIT`") 
                    split_dir = await zip7_utils.split_in_zip(path,get_val("TG_UP_LIMIT"))
                    await todel.delete()
                
                if task is not None:
                    await task.add_a_dir(split_dir)
                
                dircon = os.listdir(split_dir)
                dircon.sort()

                if not from_in:
                    updb.register_upload(message.chat_id,message.id)
                    if user_msg is None:
                        sup_mes = await message.get_reply_message()
                    else:
                        sup_mes = user_msg

                    if task is not None:
                        await task.set_message(message)
                        await task.set_original_message(sup_mes)

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
                        user_msg=user_msg,
                        task=task
                    )
                
                try:
                    shutil.rmtree(split_dir)
                    os.remove(path)
                except:pass
                
                if not from_in:
                    if updb.get_cancel_status(message.chat_id,message.id):
                        task.cancel = True
                        await task.set_inactive()
                        await message.edit("{} - Canceled By user.".format(message.text),buttons=None)
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
                    
                    if task is not None:
                        await task.set_message(message)
                        await task.set_original_message(sup_mes)

                    if task is not None:
                        await task.set_message(message)
                        await task.set_original_message(sup_mes)

                    data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
                    buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
                    await message.edit(buttons=buts)
                #print(updb)
                if black_list_exts(path):
                    if task is not None:
                        await task.uploaded_file(os.path.basename(path))
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
                        task.cancel = True
                        await task.set_inactive()
                        await message.edit("{} - Canceled By user.".format(message.text),buttons=None)
                    else:
                        await message.edit(buttons=None)
                    updb.deregister_upload(message.chat_id,message.id)

                if sentmsg is not None:
                    if task is not None:
                        await task.uploaded_file(os.path.basename(path))
                    files_dict[os.path.basename(path)] = sentmsg.id

        return files_dict