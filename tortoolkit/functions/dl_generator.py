import re
import aiohttp
import math
import urllib.parse
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
        
    #zippyshare.com fix revert back to old. Based on https://github.com/LameLemon/ziggy
    elif 'zippyshare.com' in url:
        try:
            link = re.findall(r'\bhttps?://.*zippyshare\.com\S+', url)[0]
            async with aiohttp.ClientSession() as ttksess:
                resp = await ttksess.get(link)
                restext = await resp.text()
                
            base_url = re.search('http.+.com', restext).group()
            page_soup = BeautifulSoup(restext, 'lxml')
            scripts = page_soup.find_all("script", {"type": "text/javascript"})
            for script in scripts:
                if "getElementById('dlbutton')" in script.text:
                    url_raw = re.search(r'= (?P<url>\".+\" \+ (?P<math>\(.+\)) .+);',
                                        script.text).group('url')
                    math = re.search(r'= (?P<url>\".+\" \+ (?P<math>\(.+\)) .+);',
                       script.text).group('math')
                    url = url_raw.replace(math, '"' + str(eval(math)) + '"')
                    break
            ourl = base_url + eval(url)
            name = urllib.parse.unquote(url.split('/')[-1])
            return ourl
        except:
            return "**ERROR: No zippyshare link found.**"
        
    #racaty.net
    elif 'racaty.net' in url:
        try:
            link = re.findall(r'\bhttps?://.*racaty\.net\S+', url)[0]
            async with aiohttp.ClientSession() as ttksess:
                resp = await ttksess.get(link)
                restext = await resp.text()
                
            bss=BeautifulSoup(restext,'html.parser')
            op=bss.find('input',{'name':'op'})['value']
            id=bss.find('input',{'name':'id'})['value']
                  
            async with aiohttp.ClientSession() as ttksess:
                rep = await ttksess.post(link,data={'op':op,'id':id})
                reptext = await rep.text()
                
            bss2=BeautifulSoup(reptext,'html.parser')
            ourl = bss2.find('a',{'id':'uniqueExpirylink'})['href']
            return ourl
        except:
            return "**ERROR: No racaty link found.**"
        
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
