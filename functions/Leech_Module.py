import re,os
from telethon.tl import types
import logging
from . import QBittorrentWrap
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("telethon").setLevel(logging.WARNING)

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

async def check_link(msg):
    urls = None
    omess = msg
    msg = await msg.get_reply_message()

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
            path = await msg.download_media()
            rval =  await QBittorrentWrap.register_torrent(path,rmess,file=True)
            try:
                os.remove(path)
            except:pass
            return rval
        else:
            await omess.reply("This is not a torrent file to leech from. Send <code>.torrent</code> file",parse_mode="html")

    elif msg.text is not None:
        if msg.text.lower().startswith("magnet:"):
            #urls.extend(await get_magnets(msg.text))
            rmess = await omess.reply("Scanning....")
            mgt = get_magnets(msg.text.strip())
            return await QBittorrentWrap.register_torrent(mgt,rmess,True)
        elif msg.entities is not None:
           url = get_entities(msg)
           #todo implement direst links ;)
        else:
            #consider it as a direct link LOL
            urls.append(msg.text.strip())
    
    return None

async def cancel_torrent(hashid):
    await QBittorrentWrap.deregister_torrent(hashid)