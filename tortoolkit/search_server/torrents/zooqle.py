from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class Zooqle:

    def __init__(self):
        self.BASE_URL = 'https://zooqle.com'
        self.LIMIT = None

    def _parser(self, htmls):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')

                my_dict = {
                    'data': []
                }

                for tr in soup.find_all('tr')[1:]:
                    td = tr.find_all("td")
                    name = td[1].find('a').get_text(strip=True)
                    if name != '':
                        magnet = td[2].find_all('a')[1]['href']
                        try:
                            size = td[3].find_all('div')[1].text
                        except IndexError:
                            size = None
                        url = td[1].find_all('a')[0]['href']
                        date = td[4].get_text(strip=True)
                        seeders_leechers = td[5].find(
                            'div')['title'].split('|')
                        seeders = seeders_leechers[0].replace(
                            'Seeders: ', '').strip()
                        leechers = seeders_leechers[1].replace(
                            'Leechers: ', '').strip()
                        my_dict['data'].append({
                            'name': name,
                            'size': size,
                            'seeders': seeders,
                            'leechers': leechers,
                            'hash': re.search(r'([{a-f\d,A-F\d}]{32,40})\b', magnet).group(0),
                            'magnet': magnet,
                            'url': self.BASE_URL + url,
                            'date': date,

                        })
                    if len(my_dict['data']) == self.LIMIT:
                        break
                try:
                    ul = soup.find('ul', class_='pagination')
                    tpages = ul.find_all('a')[-3].text
                    current_page = (
                        ul.find('li', class_='active')).find('a').text
                    my_dict['current_page'] = int(current_page)
                    my_dict['total_pages'] = int(tpages)
                except:
                    my_dict['current_page'] = None
                    my_dict['total_pages'] = None
                return my_dict
        except:
            return None

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + \
                '/search?pg={1}&q={0}&v=t'.format(query, page)
            return await self.parser_result(start_time, url, session)

    async def parser_result(self, start_time, url, session):
        html = await Scraper().get_all_results(session, url)
        results = self._parser(html)
        if results != None:
            results['time'] = time.time() - start_time
            results['total'] = len(results['data'])
            return results
        return results
