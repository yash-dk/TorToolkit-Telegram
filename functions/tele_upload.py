import os,logging,time
from ..core.getVars import get_val
from .progress_for_telethon import progress 


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
            pass
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
    
    file_name = os.path.basename(path)
    
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
        out_msg = await msg.client.send_file(
            msg.to_id,
            file=path,
            caption=file_name,
            reply_to=message.id,
            progress_callback=lambda c,t: progress(c,t,msg,file_name,start_time)
        )
    await msg.delete()
    return out_msg


