import re
import aiohttp
import urllib.parse
import logging
from bs4 import BeautifulSoup
from ..core.base_task import BaseTask

torlog = logging.getLogger(__name__)

class DLGen(BaseTask):
    def __init__(self):
        super().__init__()

    async def generate_directs(self, url):
        #blocklinks
        if 'mega.nz' in url or 'drive.google.com' in url or 'uptobox.com' in url \
        or '1fiecher.com' in url or 'googleusercontent.com' in url:
            self._is_errored = True
            self._error_reason = "**ERROR:** Unsupported URL!"
            return False
        
        #mediafire.com
        elif 'mediafire.com' in url:
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
                self._is_errored = True
                self._error_reason = "**ERROR:** Cant't download, double check your mediafire link!"
                return False
            
        #disk.yandex.com    
        elif 'yadi.sk' in url or 'disk.yandex.com' in url:
            try:
                link = re.findall(r'\b(https?://.*(yadi|disk)\.(sk|yandex)*(|com)\S+)', url)[0][0]
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

        #zippyshare.com
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
                self._is_errored = True
                self._error_reason = "**ERROR:** Cant't download, double check your zippyshare link!"
                return False
        
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
                self._is_errored = True
                self._error_reason = "**ERROR:** Cant't download, double check your racaty link!"
                return False
        
        elif 'pixeldrain.com' in url:
            url = url.strip("/ ")
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
        else:
            return False
    
    def cancel(self, is_admin=False):
        pass
    
    async def get_update(self):
        pass
    
    def get_error_reason(self):
        return self._error_reason