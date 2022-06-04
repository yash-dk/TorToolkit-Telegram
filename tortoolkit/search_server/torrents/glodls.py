from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class Glodls:

    def __init__(self):
        self.BASE_URL = 'https://glodls.to'
        self.LIMIT = None

    def _parser(self, htmls):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')

                my_dict = {
                    'data': []
                }
                for tr in soup.find_all('tr', class_='t-row')[0:-1:2]:
                    td = tr.find_all('td')
                    name = td[1].find_all('a')[-1].find('b').text
                    url = self.BASE_URL + td[1].find_all('a')[-1]['href']
                    torrent = self.BASE_URL + td[2].find('a')['href']
                    magnet = td[3].find('a')['href']
                    size = td[4].text
                    seeders = td[5].find('font').find('b').text
                    leechers = td[6].find('font').find('b').text
                    try:
                        uploader = td[7].find('a').find('b').find('font').text
                    except:
                        uploader = ''
                    my_dict['data'].append({
                        'name': name,
                        'size': size,
                        'uploader': uploader,
                        'seeders': seeders,
                        'leechers': leechers,
                        'magnet': magnet,
                        'torrent': torrent,
                        'url': self.BASE_URL + url,
                    })
                    if len(my_dict['data']) == self.LIMIT:
                        break
                try:
                    pagination = soup.find('div', class_='pagination')
                    total_pages = pagination.find_all('a')[-2]['href']
                    total_pages = total_pages.split("=")[-1]
                    my_dict['total_pages'] = int(total_pages) + 1
                except:
                    pass
                return my_dict
        except:
            return None

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + \
                '/search_results.php?search={}&cat=0&incldead=0&inclexternal=0&lang=0&sort=seeders&order=desc&page={}'.format(
                    query, page-1)
            return await self.parser_result(start_time, url, session)

    async def parser_result(self, start_time, url, session):
        html = await Scraper().get_all_results(session, url)
        results = self._parser(html)
        if results != None:
            results['time'] = time.time() - start_time
            results['total'] = len(results['data'])
            return results
        return results

    async def trending(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + '/today.php'
            return await self.parser_result(start_time, url, session)

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + '/search.php'
            return await self.parser_result(start_time, url, session)
