from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class TorrentGalaxy:

    def __init__(self):
        self.BASE_URL = 'https://torrentgalaxy.to'
        self.LIMIT = None

    def _parser(self, htmls):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')

                my_dict = {
                    'data': []
                }
                for idx, divs in enumerate(soup.find_all('div', class_='tgxtablerow')):
                    div = divs.find_all("div")
                    try:
                        name = div[4].find('a').get_text(strip=True)
                    except:
                        name = (div[1].find('a', class_='txlight')).find(
                            'b').text
                    if name != '':
                        try:
                            magnet = div[5].find_all('a')[1]['href']
                            torrent = div[5].find_all('a')[0]['href']
                        except:
                            magnet = div[3].find_all('a')[1]['href']
                            torrent = div[3].find_all('a')[0]['href']

                        size = soup.select(
                            'span.badge.badge-secondary.txlight')[idx].text
                        try:
                            url = div[4].find('a')['href']
                        except:
                            url = div[1].find('a', class_='txlight')['href']
                        try:
                            date = div[12].get_text(strip=True)
                        except:
                            date = div[10].get_text(strip=True)
                        try:
                            seeders_leechers = div[11].find_all('b')
                            seeders = seeders_leechers[0].text
                            leechers = seeders_leechers[1].text
                        except:
                            seeders_leechers = div[11].find_all('b')
                            seeders = seeders_leechers[0].text
                            leechers = seeders_leechers[1].text
                        try:
                            uploader = (div[7].find('a')).find('span').text
                        except:
                            uploader = (div[5].find('a')).find('span').text
                        try:
                            category = (div[0].find('small').text.replace(
                                '&nbsp', '')).split(':')[0]
                        except:
                            category = None
                        my_dict['data'].append({
                            'name': name,
                            'size': size,
                            'seeders': seeders,
                            'leechers': leechers,
                            'category': category,
                            'uploader': uploader,
                            'hash': re.search(r'([{a-f\d,A-F\d}]{32,40})\b', magnet).group(0),
                            'magnet': magnet,
                            'torrent': torrent,
                            'url': self.BASE_URL + url,
                            'date': date,

                        })
                    if len(my_dict['data']) == self.LIMIT:
                        break
                try:
                    ul = soup.find_all('ul', class_='pagination')[-1]
                    tpages = ul.find_all('li')[-2]
                    my_dict['current_page'] = int(soup.select_one(
                        'li.page-item.active.txlight a').text.split(" ")[0])
                    my_dict['total_pages'] = int(tpages.find('a').text)
                except:
                    my_dict['current_page'] = None
                    my_dict['total_pages'] = None
                    # pass
                return my_dict
        except:
            return None

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + \
                '/torrents.php?search=+{}&sort=seeders&order=desc&page={}'.format(
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
            url = self.BASE_URL
            return await self.parser_result(start_time, url, session)

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            if not category:
                url = self.BASE_URL + '/latest'
            else:
                if category == 'documentaries':
                    category = "Docus"
                url = self.BASE_URL + \
                    "/torrents.php?parent_cat={}&sort=id&order=desc&page={}".format(
                        str(category).capitalize(), page-1)
            return await self.parser_result(start_time, url, session)

    #! Maybe Implemented in Future
