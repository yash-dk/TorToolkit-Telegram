import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class TorrentFunk:

    def __init__(self):
        self.BASE_URL = 'https://www.torrentfunk.com'
        self.LIMIT = None

    @decorator_asyncio_fix
    async def _individual_scrap(self, session, url, obj):
        try:
            async with session.get(url) as res:
                html = await res.text(encoding="ISO-8859-1")
                soup = BeautifulSoup(html, 'lxml')
                try:
                    obj['torrent'] = soup.select_one(
                        '#right > main > div.content > table:nth-child(3) > tr > td:nth-child(2) > a')['href']
                    obj['category'] = soup.select_one(
                        '#right > main > div.content > table:nth-child(7) > tr> td:nth-child(2) > a').text
                    obj['hash'] = soup.select_one(
                        '#right > main > div.content > table:nth-child(7) > tr:nth-child(3) > td:nth-child(2)').text
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

                for tr in soup.select('.tmain tr')[idx:]:
                    td = tr.find_all("td")
                    if len(td) == 0:
                        continue
                    name = td[0].find('a').text
                    date = td[1].text
                    size = td[2].text
                    seeders = td[3].text
                    leechers = td[4].text
                    uploader = td[5].text
                    url = self.BASE_URL + td[0].find('a')['href']
                    list_of_urls.append(url)
                    my_dict['data'].append({
                        'name': name,
                        'size': size,
                        'date': date,
                        'seeders': seeders,
                        'leechers': leechers,
                        'uploader': uploader if uploader else None,
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
                "/all/torrents/{}/{}.html".format(query, page)
            return await self.parser_result(start_time, url, session, idx=6)

    async def parser_result(self, start_time, url, session, idx=1):
        htmls = await Scraper().get_all_results(session, url)
        result, urls = self._parser(htmls, idx)
        if result:
            results = await self._get_torrent(result, session, urls)
            results['time'] = time.time() - start_time
            results['total'] = len(results['data'])
            return results
        return result

    async def trending(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL
            return await self.parser_result(start_time, url, session)

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            if not category:
                url = self.BASE_URL + '/movies/recent.html'
            else:
                if category == 'apps':
                    category = 'software'
                elif category == 'tv':
                    category = 'television'
                elif category == 'books':
                    category = 'ebooks'
                url = self.BASE_URL + \
                    "/{}/recent.html".format(category)
            return await self.parser_result(start_time, url, session)
