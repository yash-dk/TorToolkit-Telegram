import re
import aiohttp
import math
import logging
from bs4 import BeautifulSoup

torlog = logging.getLogger(__name__)

async def generate_directs(url):
    #Mediafire
    if 'mediafire.com' in url:
        try:
            link = re.findall(r'\bhttps?://.*mediafire\.com\S+', url)[0]
            async with aiohttp.ClientSession() as ttksess:
                resp = await ttksess.get(link)
                restext = await resp.text()
            
            page = BeautifulSoup(restext, 'lxml')
            info = page.find('a', {'aria-label': 'Download file'})
            ourl = info.get('href')
            return ourl
        except:
            return "**ERROR No mediafire link found.**"
        
        
    #Zippyshare
    elif  'zippyshare.com' in url:
        
        #Zippyshare fix directlink generator for ttk by @yourtulloh based on:
        #Zippyshare up-to-date plugin from https://github.com/UsergeTeam/Userge-Plugins/blob/master/plugins/zippyshare.py
        #Thanks to all contributors @aryanvikash, rking32, @BianSepang
        tulloh = r'https://www(\d{1,3}).zippyshare.com/v/(\w{8})/file.html'
        regex_result = (
            r'var a = (\d{6});\s+var b = (\d{6});\s+document\.getElementById'
            r'\(\'dlbutton\'\).omg = "f";\s+if \(document.getElementById\(\''
            r'dlbutton\'\).omg != \'f\'\) {\s+a = Math.ceil\(a/3\);\s+} else'
            r' {\s+a = Math.floor\(a/3\);\s+}\s+document.getElementById\(\'d'
            r'lbutton\'\).href = "/d/[a-zA-Z\d]{8}/\"\+\(a \+ \d{6}%b\)\+"/('
            r'[\w%-.]+)";'
        )
        
        match = re.match(tulloh, url)
        if not match:
            return "**ERROR Invalid Zippyshare URL.**"
        
        server, id_ = match.group(1), match.group(2)
        async with aiohttp.ClientSession() as ttksess:
            resp = await ttksess.get(url)
            restext = await resp.text()
            
        match = re.search(regex_result, restext, re.DOTALL)
        if not match:
            return "**ERROR Invalid response, try again!**"
        
        val_1 = int(match.group(1))
        val_2 = math.floor(val_1 / 3)
        val_3 = int(match.group(2))
        val = val_1 + val_2 % val_3
        name = match.group(3)
        ourl = "https://www{}.zippyshare.com/d/{}/{}/{}".format(server, id_, val, name)
        return ourl
        
    elif 'yadi.sk' in url or 'disk.yandex.com' in url:
        try:
            link = re.findall(r'\b(https?://.*(yadi|disk)\.(sk|yandex)*(|com)\S+)', url)[0][0]
            print(link)
        except:
            return "**ERROR No yadisk link found.**"

        api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}'
        try:
            async with aiohttp.ClientSession() as ttksess:
                resp = await ttksess.get(api.format(link))
                restext = await resp.json()
                ourl = restext['href']
                return ourl
        except:
            torlog.exception("Ayee jooo")
            return "**ERROR 404 File Not Found** or \n**Download limit reached.**"