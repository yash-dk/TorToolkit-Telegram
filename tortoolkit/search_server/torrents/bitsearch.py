from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class Bitsearch:

    def __init__(self):
        self.BASE_URL = 'https://bitsearch.to'
        self.LIMIT = None

    def _parser(self, htmls):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')

                my_dict = {
                    'data': []
                }
                for divs in soup.find_all('li', class_='search-result'):
                    info = divs.find("div", class_='info')
                    name = info.find('h5', class_='title').find('a').text
                    url = info.find('h5', class_='title').find('a')['href']
                    category = info.find('div').find(
                        'a', class_='category').text
                    stats = info.find('div', class_='stats').find_all('div')
                    if stats:
                        downloads = stats[0].text
                        size = stats[1].text
                        seeders = stats[2].text.strip()
                        leechers = stats[3].text.strip()
                        date = stats[4].text
                        links = divs.find("div", class_='links').find_all('a')
                        magnet = links[1]['href']
                        torrent = links[0]['href']
                        my_dict['data'].append({
                            'name': name,
                            'size': size,
                            'seeders': seeders,
                            'leechers': leechers,
                            'category': category,
                            'hash': re.search(r'([{a-f\d,A-F\d}]{32,40})\b', magnet).group(0),
                            'magnet': magnet,
                            'torrent': torrent,
                            'url': self.BASE_URL + url,
                            'date': date,
                            'downloads': downloads

                        })
                    if len(my_dict['data']) == self.LIMIT:
                        break
                try:
                    total_pages = int(soup.select(
                        'body > main > div.container.mt-2 > div > div:nth-child(1) > div > span > b')[0].text) / 20  # !20 search result available on each page
                    total_pages = total_pages + \
                        1 if type(total_pages) == float else total_pages if int(
                            total_pages) > 0 else total_pages + 1

                    current_page = int(soup.find('div', class_='pagination').find(
                        'a', class_='active').text)
                    my_dict['current_page'] = current_page
                    my_dict['total_pages'] = int(total_pages)
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
                '/search?q={}&page={}'.format(
                    query, page)
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
            url = self.BASE_URL + '/trending'
            return await self.parser_result(start_time, url, session)
