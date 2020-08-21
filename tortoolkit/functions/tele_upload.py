import os,logging,time,traceback
from ..core.getVars import get_val
from ..core import thumb_manage # i guess i will dodge this one ;) as i am importing the vids helper anyways
from . import vids_helpers
from .progress_for_telethon import progress
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from telethon.errors import VideoContentTypeInvalidError
from ..core.database_handle import TtkUpload
from telethon.tl.types import KeyboardButtonCallback
from .Ftele import upload_file

torlog = logging.getLogger(__name__)

#thanks @SpEcHlDe for this concept of recursion
async def upload_handel(path,message,from_uid,files_dict,job_id=0,force_edit=False,updb=None,from_in=False):
    # creting here so connections are kept low
    if updb is None:
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
            sup_mes = await message.get_reply_message()
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
                from_in=True
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
            del_mes = await message.reply("FILE LAGRE THEN THRESHOLD SPLITTING NOW.Processing.....") 
            split_dir = await vids_helpers.split_file(path,get_val("TG_UP_LIMIT"))
            dircon = os.listdir(split_dir)
            dircon.sort()

            if not from_in:
                updb.register_upload(message.chat_id,message.id)
                sup_mes = await message.get_reply_message()
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
                    from_in=True
                )

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
                sup_mes = await message.get_reply_message()
                data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
                buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
                await message.edit(buttons=buts)
            print(updb)
            sentmsg = await upload_a_file(
                path,
                message,
                force_edit,
                updb
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



async def upload_a_file(path,message,force_edit,database=None):
    
    if database is not None:
        if database.get_cancel_status(message.chat_id,message.id):
            # add os remove here
            return None
    if not os.path.exists(path):
        return None
        
    #todo improve this uploading ✔️
    file_name = os.path.basename(path)
    metadata = extractMetadata(createParser(path))
    
    metadata = metadata.exportDictionary()
    try:
        mime = metadata.get("Common").get("MIME type")
    except:
        mime = metadata.get("Metadata").get("MIME type")

    ftype = mime.split("/")[0]
    ftype = ftype.lower().strip()
    


    if not force_edit:
        sup_mes = await message.get_reply_message()
        data = "upcancel {} {} {}".format(message.chat_id,message.id,sup_mes.sender_id)
        buts = [KeyboardButtonCallback("Cancel upload.",data.encode("UTF-8"))]
        msg = await message.reply("Uploading {}".format(file_name),buttons=buts)
    else:
        msg = message

    out_msg = None
    start_time = time.time()
    tout = get_val("EDIT_SLEEP_SECS")
    opath = path
    #with open(path,"rb") as filee:
    #    path = await upload_file(message.client,filee,file_name,
    #    lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
    #    )


    try:
        if message.media and force_edit:
            out_msg = await msg.edit(
                file=path,
                text=file_name
            )
        else:
            
            if ftype == "video":
                if get_val("FORCE_DOCUMENTS") == True:
                    # add the thumbs for the docs too
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        caption=file_name,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
                    )
                else:
                    thumb = await thumb_manage.get_thumbnail(opath)
                    try:
                        out_msg = await msg.client.send_file(
                            msg.to_id,
                            file=path,
                            thumb=thumb,
                            caption=file_name,
                            reply_to=message.id,
                            supports_streaming=True,
                            progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
                        )
                    except VideoContentTypeInvalidError:
                        torlog.warning("Streamable file send failed fallback to document.")
                        out_msg = await msg.client.send_file(
                            msg.to_id,
                            file=path,
                            caption=file_name,
                            thumb=thumb,
                            reply_to=message.id,
                            force_document=True,
                            progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
                        )
                    except Exception:
                        torlog.error("Error:- {}".format(traceback.format_exc()))
            elif ftype == "audio":
                # not sure about this if
                out_msg = await msg.client.send_file(
                    msg.to_id,
                    file=path,
                    caption=file_name,
                    reply_to=message.id,
                    progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
                )
            else:
                if get_val("FORCE_DOCUMENTS"):
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        caption=file_name,
                        reply_to=message.id,
                        force_document=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
                    )
                else:
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        caption=file_name,
                        reply_to=message.id,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time,tout,message,database)
                    )
    except Exception as e:
        if str(e).find("cancel") != -1:
            torlog.info("cancled an upload lol")
            await msg.delete()
        else:
            torlog.info(traceback.format_exc())
                

    if out_msg is None:
        return None
    if out_msg.id != msg.id:
        await msg.delete()
    
    return out_msg


