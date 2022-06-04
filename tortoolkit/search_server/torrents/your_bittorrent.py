import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class YourBittorrent:

    def __init__(self):
        self.BASE_URL = 'https://yourbittorrent.com'
        self.LIMIT = None

    @decorator_asyncio_fix
    async def _individual_scrap(self, session, url, obj):
        try:
            async with session.get(url) as res:
                html = await res.text(encoding="ISO-8859-1")
                soup = BeautifulSoup(html, 'lxml')
                try:
                    container = soup.select_one('div.card-body.container')
                    poster = container.find('div').find_all('div')[
                        0].find('picture').find('img')['src']
                    clearfix = soup.find('div', class_='clearfix')
                    torrent = clearfix.find('div').find_all('div')[
                        1].find('a')['href']
                    obj['torrent'] = torrent
                    obj['poster'] = poster
                except:
                    pass
        except:
            return None

    async def _get_torrent(self, result, session, urls):
        tasks = []
        for idx, url in enumerate(urls):
            for obj in result['data']:
                if obj['url'] == url:
                    task = asyncio.create_task(self._individual_scrap(
                        session, url, result['data'][idx]))
                    tasks.append(task)
        await asyncio.gather(*tasks)
        return result

    def _parser(self, htmls, idx=1):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')
                list_of_urls = []
                my_dict = {
                    'data': []
                }

                for tr in soup.find_all('tr')[idx:]:
                    td = tr.find_all("td")
                    name = td[1].find('a').get_text(strip=True)
                    url = self.BASE_URL + td[1].find('a')['href']
                    list_of_urls.append(url)
                    size = td[2].text
                    date = td[3].text
                    seeders = td[4].text
                    leechers = td[5].text
                    my_dict['data'].append({
                        'name': name,
                        'size': size,
                        'date': date,
                        'seeders': seeders,
                        'leechers': leechers,
                        'url': url,
                    })
                    if len(my_dict['data']) == self.LIMIT:
                        break
                return my_dict, list_of_urls
        except:
            return None, None

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + \
                "/?v=&c=&q={}".format(query)
            return await self.parser_result(start_time, url, session, idx=6)

    async def parser_result(self, start_time, url, session, idx=1):
        htmls = await Scraper().get_all_results(session, url)
        result, urls = self._parser(htmls, idx)
        if result != None:
            results = await self._get_torrent(result, session, urls)
            results['time'] = time.time() - start_time
            results['total'] = len(results['data'])
            return results
        return result

    async def trending(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            idx = None
            if not category:
                url = self.BASE_URL + '/top.html'
                idx = 1
            else:
                if category == 'books':
                    category = 'ebooks'
                url = self.BASE_URL + f"/{category}.html"
                idx = 4
            return await self.parser_result(start_time, url, session, idx)

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            idx = None
            if not category:
                url = self.BASE_URL + \
                    "/new.html"
                idx = 1
            else:
                if category == 'books':
                    category = 'ebooks'
                url = self.BASE_URL + f"/{category}/latest.html"
                idx = 4
            return await self.parser_result(start_time, url, session, idx)
