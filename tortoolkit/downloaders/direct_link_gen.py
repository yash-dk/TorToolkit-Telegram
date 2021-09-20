# -*- coding: utf-8 -*-
# (c) YashDK [yash-dk@github]
# Thanks to slam-mirrorbot for some extractor logic in this file.
import re
import aiohttp
import urllib.parse
import logging
from bs4 import BeautifulSoup
from ..core.getVars import get_val
from ..core.base_task import BaseTask

torlog = logging.getLogger(__name__)

class DLGen(BaseTask):
    def __init__(self):
        super().__init__()

    async def generate_directs(self, url):
        #blocklinks
        self._url = url
        if 'drive.google.com' in url or 'uptobox.com' in url \
        or '1fiecher.com' in url or 'googleusercontent.com' in url:
            self._is_errored = True
            self._error_reason = "**ERROR:** Unsupported URL!"
            return False
        elif 'youtube.com' in url or 'youtu.be' in url:
            return await self.youtube_in_leech()
        #mediafire.com
        elif 'mediafire.com' in url:
            return await self.mediafile_dl()
            
        #disk.yandex.com    
        elif 'yadi.sk' in url or 'disk.yandex.com' in url:
            return await self.yadisk_dl()            

        #zippyshare.com
        elif 'zippyshare.com' in url:
            return await self.zippyshare_dl()
        
        #racaty.net
        elif 'racaty.net' in url:
            return await self.racaty_dl()
        
        elif 'pixeldrain.com' in url:
            return await self.pixeldrain_dl()
        
        elif 'uptobox.com' in url:
            return await self.uptobox_dl()
        
        else:
            return False
    
    def cancel(self, is_admin=False):
        pass
    
    async def get_update(self):
        pass
    
    def get_error_reason(self):
        return self._error_reason


    # Generator Functions Below

    async def mediafile_dl(self):
        try:
            link = re.findall(r'\bhttps?://.*mediafire\.com\S+', self._url)[0]
            async with aiohttp.ClientSession() as ttksess:
                resp = await ttksess.get(link)
                restext = await resp.text()
        
            page = BeautifulSoup(restext, 'lxml')
            info = page.find('a', {'aria-label': 'Download file'})
            ourl = info.get('href')
            return ourl
        except:
            self._is_errored = True
            self._error_reason = "**ERROR:** Cant't download, double check your mediafire link!"
            return False

    async def yadisk_dl(self):
        try:
            link = re.findall(r'\b(https?://.*(yadi|disk)\.(sk|yandex)*(|com)\S+)', self._url)[0][0]
            print(link)
        except:
            self._is_errored = True
            self._error_reason = "**ERROR:** Cant't download, double check your yadisk link!"
            return False
        
        api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}'
        try:
            async with aiohttp.ClientSession() as ttksess:
                resp = await ttksess.get(api.format(link))
                restext = await resp.json()
                ourl = restext['href']
                return ourl
        except:
            torlog.exception("Ayee jooo")
            self._is_errored = True
            self._error_reason = "**ERROR:** Cant't download, the yadisk file not found or dowmload limit reached!" 
            return False

    async def zippyshare_dl(self):
        try:
            link = re.findall(r'\bhttps?://.*zippyshare\.com\S+', self._url)[0]
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
            self._is_errored = True
            self._error_reason = "**ERROR:** Cant't download, double check your zippyshare link!"
            return False

    async def racaty_dl(self):
        try:
            link = re.findall(r'\bhttps?://.*racaty\.net\S+', self._url)[0]
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
            self._is_errored = True
            self._error_reason = "**ERROR:** Cant't download, double check your racaty link!"
            return False

    async def pixeldrain_dl(self):
        url = self._url.strip("/ ")
        file_id = url.split("/")[-1]
        
        info_link = f"https://pixeldrain.com/api/file/{file_id}/info"
        dl_link = f"https://pixeldrain.com/api/file/{file_id}"
        
        async with aiohttp.ClientSession() as ttksess:
            resp = await ttksess.get(info_link)
            restext = await resp.json()
        
        if restext["success"]:
            return dl_link
        else:
            self._is_errored = True
            self._error_reason = "**ERROR:** Cant't download, {}.".format(restext["value"])
            return False

    async def youtube_in_leech(self):
        self._is_errored = True
        self._error_reason = "**ERROR:** Use ytdl/pytdl commands to download the Youtube links."
        return False
    
    async def uptobox_dl(self):
        try:
            link = re.findall(r'\bhttps?://.*uptobox\.com\S+', self._url)[0]
        except IndexError:
            self._is_errored = True
            self._error_reason = "**ERROR:** Cant't find download link."
            return False
        
        if get_val("UPTOBOX_TOKEN") is None:
            torlog.error('UPTOBOX_TOKEN not provided!')
            dl_url = link
        else:
            try:
                link = re.findall(r'\bhttp?://.*uptobox\.com/dl\S+', self._url)[0]
                dl_url = link
            except:
                file_id = re.findall(r'\bhttps?://.*uptobox\.com/(\w+)', self._url)[0]
                file_link = 'https://uptobox.com/api/link?token={}&file_code={}'.format(get_val("UPTOBOX_TOKEN"), file_id)
                async with aiohttp.ClientSession() as ttksess:
                    resp = await ttksess.get(file_link)
                    result = await resp.text()        
                
                dl_url = result['data']['dlLink']
        return dl_url

# TODO
# add the UPTOBOX_TOKEN in getvar 