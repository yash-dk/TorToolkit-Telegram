import os,logging,time,traceback
from ..core.getVars import get_val
from ..core import thumb_manage # i guess i will dodge this one ;) as i am importing the vids helper anyways
from . import vids_helpers
from .progress_for_telethon import progress
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from telethon.errors import VideoContentTypeInvalidError

torlog = logging.getLogger(__name__)

#thanks @SpEcHlDe for this concept of recursion
async def upload_handel(path,message,from_uid,files_dict,job_id=0,force_edit=False):
    #logging.info("Uploading Now:- {}".format(path))

    if os.path.isdir(path):
        logging.info("Uplaoding the directory:- {}".format(path))

        directory_contents = os.listdir(path)
        directory_contents.sort()
        message = await message.reply("{}\nFound {} files for this download".format(message.text,len(directory_contents)))

        for file in directory_contents:
            await upload_handel(
                os.path.join(path,file),
                message,
                from_uid,
                files_dict,
                force_edit
            )
    else:
        logging.info("Uplaoding the directory:- {}".format(path))
        if os.path.getsize(path) > get_val("TG_UP_LIMIT"):
            split_dir = await vids_helpers.split_file(path,get_val("TG_UP_LIMIT"))
            dircon = os.listdir(split_dir)
            dircon.sort()

            for file in dircon:
                await upload_handel(
                    os.path.join(split_dir,file),
                    message,
                    from_uid,
                    files_dict
                )
            # spliting file logic blah blah
        else:
            sentmsg = await upload_a_file(
                path,
                message,
                force_edit
            )
            if sentmsg is not None:
                files_dict[os.path.basename(path)] = sentmsg.id

    return files_dict

async def upload_a_file(path,message,force_edit):
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
        msg = await message.reply("Uploading {}".format(file_name))
    else:
        msg = message

    
    if message.media and force_edit:
        out_msg = await msg.edit(
            file=path,
            text=file_name
        )
    else:
        start_time = time.time()
        if ftype == "video":
            if get_val("FORCE_DOCUMENTS") == True:
                out_msg = await msg.client.send_file(
                    msg.to_id,
                    file=path,
                    caption=file_name,
                    reply_to=message.id,
                    force_document=True,
                    progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time)
                )
            else:
                thumb = await thumb_manage.get_thumbnail(path)
                try:
                    out_msg = await msg.client.send_file(
                        msg.to_id,
                        file=path,
                        thumb=thumb,
                        caption=file_name,
                        reply_to=message.id,
                        supports_streaming=True,
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time)
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
                        progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time)
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
                progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time)
            )
        else:
            out_msg = await msg.client.send_file(
                msg.to_id,
                file=path,
                caption=file_name,
                reply_to=message.id,
                force_document=True,
                progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time)
            )
            
    if out_msg.id != msg.id:
        await msg.delete()
    
    return out_msg


