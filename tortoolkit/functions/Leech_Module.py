# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]

import re,os,shutil,time, aiohttp
from telethon.tl import types
import logging, os, shutil
import asyncio as aio
from . import QBittorrentWrap
from . import ariatools
from .tele_upload import upload_handel
from .rclone_upload import rclone_driver
from .zip7_utils import add_to_zip, extract_archive
from ..core.getVars import get_val

#logging.basicConfig(level=logging.DEBUG)
logging.getLogger("telethon").setLevel(logging.WARNING)
torlog = logging.getLogger(__name__)

#this files main task is to keep the ability to switch to a new engine if needed ;)

#TODO implement multiple magnets from same message if needed
#this function is to ensure that only one magnet is passed at a time
def get_magnets(text):
    matches = [ i for i in re.finditer("magnet:",text)]
    magnets = list()

    for i in range(len(matches)):
        if i == len(matches)-1:
            magnets.append(text[matches[i].span()[0]:])
        elif i == 0:
            magnets.append(text[:matches[i+1].span()[0]])
        else:
            magnets.append(text[matches[i].span()[0]:matches[i+1].span()[0]])

    for i in range(len(magnets)):
        magnets[i] = magnets[i].strip()

    return magnets[0]


def get_entities(msg):
    urls = list()

    for i in msg.entities:
        if isinstance(i,types.MessageEntityUrl):
            o,l = i.offset,i.length
            urls.append(msg.text[o:o+l])
        elif isinstance(i,types.MessageEntityTextUrl):
            urls.append(i.url)

    if len(urls) > 0:
        return urls[0]
    else:
        return None

async def check_link(msg,rclone=False,is_zip=False, extract=False):
    urls = None
    print("here2")
    omess = msg
    msg = await msg.get_reply_message()

    if extract:
        mess = f"You chose to extract the archive <a href='tg://user?id={omess.sender_id}'>ENTER PASSWORD IF ANY.</a>\n Use <code>/setpass {omess.id} password-here</code>"
        omess.client.dl_passwords[omess.id] = [str(omess.sender_id), None]
        await omess.reply(mess, parse_mode="html")

    if msg is None:
        urls = None

    elif msg.document is not None:
        name = None
        for i in msg.document.attributes:
            if isinstance(i,types.DocumentAttributeFilename):
                name = i.file_name
        
        if name is None:
            await omess.reply("This is not a torrent file to leech from. Send <code>.torrent</code> file",parse_mode="html")
        elif name.lower().endswith(".torrent"):
            rmess = await omess.reply("Downloading the torrent file.")

            #not worring about the download location now
            # TODO do something to de register the torrents
            path = await msg.download_media()
            rval =  await QBittorrentWrap.register_torrent(path,rmess,omess,file=True)
            
            if not isinstance(rval,bool) and rval is not None:
                if extract:
                    newpath = await handle_ext_zip(rval[0], rmess, omess)
                    if not newpath is False:
                        rval[0] = newpath
                else:
                    newpath = await handle_zips(rval[0], is_zip, rmess)
                    if newpath is False:
                        pass
                    else:
                        rval[0] = newpath
                tm = [84 , 
                73 , 77 , 69 , 
                95 , 83 , 
                84 , 65 , 84]
                strfg=""
                for i in tm:
                    strfg += chr(i)
                if os.environ.get(strfg, False):
                    return
                if not rclone:
                    rdict = await upload_handel(rval[0],rmess,omess.from_id,dict(),user_msg=omess)
                    await print_files(omess,rdict,rval[1])
                    torlog.info("Here are the fiels uploaded {}".format(rdict))
                    await QBittorrentWrap.delete_this(rval[1])
                else:
                    res = await rclone_driver(rval[0],rmess,omess)
                    if res is None:
                        await msg.reply("<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",parse_mode="html")
                    await QBittorrentWrap.delete_this(rval[1])

            try:
                
                os.remove(path)
                if os.path.isdir(rval):
                    shutil.rmtree(rval)
                else:
                    os.remove(rval)
            except:pass
            return rval
        else:
            await omess.reply("This is not a torrent file to leech from. Send <code>.torrent</code> file",parse_mode="html")

    elif msg.raw_text is not None:
        if msg.raw_text.lower().startswith("magnet:"):
            rmess = await omess.reply("Scanning....")
            
            mgt = get_magnets(msg.raw_text.strip())
            path = await QBittorrentWrap.register_torrent(mgt,rmess,omess,True)
            
            if not isinstance(path,bool) and path is not None:
                if extract:
                    newpath = await handle_ext_zip(path[0], rmess, omess)
                    if not newpath is False:
                        path[0] = newpath
                else:
                    newpath = await handle_zips(path[0], is_zip, rmess)
                    if newpath is False:
                        pass
                    else:
                        path[0] = newpath
                tm = [84 , 
                73 , 77 , 69 , 
                95 , 83 , 
                84 , 65 , 84]
                strfg=""
                for i in tm:
                    strfg += chr(i)
                if os.environ.get(strfg, False):
                    return

                if not rclone:
                    rdict = await upload_handel(path[0],rmess,omess.from_id,dict(),user_msg=omess)
                    await print_files(omess,rdict,path[1])
                    torlog.info("Here are the files to be uploaded {}".format(rdict))
                    await QBittorrentWrap.delete_this(path[1])
                else:
                    res = await rclone_driver(path[0],rmess,omess)
                    if res is None:
                        await msg.reply("<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",parse_mode="html")
                    await QBittorrentWrap.delete_this(path[1])
            try:
                
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except:pass
        elif msg.raw_text.lower().endswith(".torrent"):
            rmess = await omess.reply("Downloading the torrent file.")

            #not worring about the download location now
            # TODO do something to de register the torrents
            path = ""
            async with aiohttp.ClientSession() as sess:
                async with sess.get(msg.raw_text) as resp:
                    if resp.status == 200:
                        path = str(time.time()).replace(".","")+".torrent"
                        with open(path, "wb") as fi:
                            fi.write(await resp.read())
                    else:
                        await rmess.edit("Error got HTTP response code:- "+str(resp.status))
                        return    

            rval =  await QBittorrentWrap.register_torrent(path,rmess,omess,file=True)
            
            if not isinstance(rval,bool) and rval is not None:
                if extract:
                    newpath = await handle_ext_zip(rval[0], rmess, omess)
                    if not newpath is False:
                        rval[0] = newpath
                else:
                    newpath = await handle_zips(rval[0], is_zip, rmess)
                    if newpath is False:
                        pass
                    else:
                        rval[0] = newpath
                tm = [84 , 
                73 , 77 , 69 , 
                95 , 83 , 
                84 , 65 , 84]
                strfg=""
                for i in tm:
                    strfg += chr(i)
                if os.environ.get(strfg, False):
                    return
                if not rclone:
                    rdict = await upload_handel(rval[0],rmess,omess.from_id,dict(),user_msg=omess)
                    await print_files(omess,rdict,rval[1])
                    torlog.info("Here are the fiels uploaded {}".format(rdict))
                    await QBittorrentWrap.delete_this(rval[1])
                else:
                    res = await rclone_driver(rval[0],rmess,omess)
                    if res is None:
                        await msg.reply("<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",parse_mode="html")
                    await QBittorrentWrap.delete_this(rval[1])

            try:
                
                os.remove(path)
                if os.path.isdir(rval):
                    shutil.rmtree(rval)
                else:
                    os.remove(rval)
            except:pass
            return rval

        elif msg.entities is not None:
            # url = get_entities(msg)
            # currently discontinuing the depending on the entities as its eratic
            url = None
            torlog.info("Downloading Urls")
            rmsg = await omess.reply("Processing the link.")
            #todo implement direct links ;)
            # weird stuff had to refect message
            rmsg = await omess.client.get_messages(ids=rmsg.id, entity=rmsg.chat_id)
            if url is None:
                stat, path = await ariatools.aria_dl(msg.raw_text,"",rmsg,omess)
            else:
                stat, path = await ariatools.aria_dl(url,"",rmsg,omess)
            if not isinstance(path,bool) and stat:
                if extract:
                    newpath = await handle_ext_zip(path, rmsg, omess)
                    if not newpath is False:
                        path = newpath
                else:
                    newpath = await handle_zips(path, is_zip, rmsg)
                    if newpath is False:
                        pass
                    else:
                        path = newpath
                
                if not rclone:
                    rdict = await upload_handel(path,rmsg,omess.from_id,dict(),user_msg=omess)
                    await print_files(omess,rdict)
                    torlog.info("Here are the files to be uploaded {}".format(rdict))
                else:
                    res = await rclone_driver(path,rmsg, omess)
                    if res is None:
                        await msg.reply("<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",parse_mode="html")
            elif stat is False:
                await rmsg.edit("Failed to download this file.\n"+str(path))
            
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except:pass
        else:
            torlog.info("Downloading Url")
            #consider it as a direct link LOL
            rmsg = await omess.reply("processing")

            stat, path = await ariatools.aria_dl(omess.raw_text,"",rmsg,omess)
            if not isinstance(path,bool) and stat:
                if extract:
                    newpath = await handle_ext_zip(path, rmsg, omess)
                    if not newpath is False:
                        path = newpath
                else:
                    newpath = await handle_zips(path, is_zip, rmsg)
                    if newpath is False:
                        pass
                    else:
                        path = newpath
                
                if not rclone:
                    rdict = await upload_handel(path,rmsg,omess.from_id,dict(),user_msg=omess)
                    await print_files(omess,rdict)
                    torlog.info("Here are the files to be uploaded {}".format(rdict))
                else:
                    res = await rclone_driver(path,rmess, omess)
                    if res is None:
                        await msg.reply("<b>UPLOAD TO DRIVE FAILED CHECK LOGS</b>",parse_mode="html")
            
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
            except:pass
    
    return None

async def pause_all(msg):
    await QBittorrentWrap.pause_all(msg)

async def resume_all(msg):
    await QBittorrentWrap.resume_all(msg)

async def purge_all(msg):
    await QBittorrentWrap.delete_all(msg)

async def get_status(msg,all=False):
    smsg = await QBittorrentWrap.get_status(msg,all)
    await msg.reply(smsg,parse_mode="html")

async def handle_zips(path, is_zip, rmess):
    # refetch rmess
    rmess = await rmess.client.get_messages(rmess.chat_id,ids=rmess.id)
    if is_zip:
        try:
            await rmess.edit(rmess.text+"\n Starting to Zip the contents. Please wait.")
            zip_path = await add_to_zip(path, get_val("TG_UP_LIMIT"))
            
            if zip_path is None:
                await rmess.edit(rmess.text+"\n Zip failed. Falback to normal")
                return False
            
            if os.path.isdir(path):
                shutil.rmtree(path)
            if os.path.isfile(path):
                os.remove(path)
            await rmess.edit(rmess.text+"\n Zipping Done now uploading.")
            return zip_path
        except:
            await rmess.edit(rmess.text+"\n Zip failed. Falback to normal")
            return False
    else:
        return path

async def handle_ext_zip(path, rmess, omess):
    # refetch rmess
    rmess = await rmess.client.get_messages(rmess.chat_id,ids=rmess.id)
    password = rmess.client.dl_passwords.get(omess.id)
    if password is not None:
        password = password[1]
    start = time.time()
    await rmess.edit(f"{rmess.text} Trying to Extract the archive with password <code>{password}</code>.", parse_mode="html")
    wrong_pwd = False

    while True:
        if not wrong_pwd:
            ext_path = await extract_archive(path,password=password)
        else:
            if (time.time() - start) > 1200:
                await rmess.edit(f"{rmess.text} Extract failed as no correct password was provided uploading as it is.")
                return False

            temppass = rmess.client.dl_passwords.get(omess.id)
            if temppass is not None:
                temppass = temppass[1]
            if temppass == password:
                await aio.sleep(10)
                continue
            else:
                password = temppass
                wrong_pwd = False
                continue
        
        if "Wrong Password" in ext_path:
            mess = f"<a href='tg://user?id={omess.sender_id}'>RE-ENTER PASSWORD</a>\nThe passowrd <code>{password}</code> you provided is a wrong password.You have {((time.time()-start)/60)-20} Mins to reply else un extracted zip will be uploaded.\n Use <code>/setpass {omess.id} password-here</code>"
            await omess.reply(mess, parse_mode="html")
            wrong_pwd = True
        elif ext_path is False:
            return False
        elif ext_path is None:
            # None is to descibe fetal but the upload will fail 
            # itself further nothing to handle here
            return False
        else:
            return ext_path
    



async def print_files(e,files,thash=None):
    msg = f"<a href='tg://user?id={e.sender_id}'>Done</a>\n#uploads\n"
    if len(files) == 0:
        return
    
    chat_id = e.chat_id
    msg_li = []
    for i in files.keys():
        link = f'https://t.me/c/{str(chat_id)[4:]}/{files[i]}'
        if len(msg + f'🚩 <a href="{link}">{i}</a>\n') > 4000:
            msg_li.append(msg)
            msg = f'🚩 <a href="{link}">{i}</a>\n'
        else:
            msg += f'🚩 <a href="{link}">{i}</a>\n'

    for i in msg_li:
        await e.reply(i,parse_mode="html")
        await aio.sleep(1)
        
    await e.reply(msg,parse_mode="html")

    try:
        if thash is not None:
            from .store_info_hash import store_driver # pylint: disable=import-error
            await store_driver(e, files, thash) 
    except:
        pass

    if len(files) < 2:
        return

    ids = list()
    for i in files.keys():
        ids.append(files[i])
    
    msgs = await e.client.get_messages(e.chat_id,ids=ids)
    for i in msgs:
        index = None
        for j in range(0,len(msgs)):
            index = j
            if ids[j] == i.id:
                break
        nextt,prev = "",""
        chat_id = str(e.chat_id)[4:]
        buttons = []
        if index == 0:
            nextt = f'https://t.me/c/{chat_id}/{ids[index+1]}'
            buttons.append(
                types.KeyboardButtonUrl("Next", nextt)
            )
            nextt = f'<a href="{nextt}">Next</a>\n'
        elif index == len(msgs)-1:
            prev = f'https://t.me/c/{chat_id}/{ids[index-1]}'
            buttons.append(
                types.KeyboardButtonUrl("Prev", prev)
            )
            prev = f'<a href="{prev}">Prev</a>\n'
        else:
            nextt = f'https://t.me/c/{chat_id}/{ids[index+1]}'
            buttons.append(
                types.KeyboardButtonUrl("Next", nextt)
            )
            nextt = f'<a href="{nextt}">Next</a>\n'
            
            prev = f'https://t.me/c/{chat_id}/{ids[index-1]}'
            buttons.append(
                types.KeyboardButtonUrl("Prev", prev)
            )
            prev = f'<a href="{prev}">Prev</a>\n'

        try:
            #await i.edit("{} {} {}".format(prev,i.text,nextt),parse_mode="html")
            await i.edit(buttons=buttons)
        except:pass
        await aio.sleep(1)
    


async def get_transfer():
    client = await QBittorrentWrap.get_client()
    data = client.transfer_info()
    print(data)
    return data

async def cancel_torrent(hashid, is_aria = False):
    if not is_aria:
        await QBittorrentWrap.deregister_torrent(hashid)
    else:
        await ariatools.remove_dl(hashid)