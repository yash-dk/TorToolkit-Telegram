import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class Limetorrent:

    def __init__(self):
        self.BASE_URL = 'https://www.limetorrents.pro'
        self.LIMIT = None

    @decorator_asyncio_fix
    async def _individual_scrap(self, session, url, obj):
        try:
            async with session.get(url) as res:
                html = await res.text(encoding="ISO-8859-1")
                soup = BeautifulSoup(html, 'lxml')
                try:
                    a_tag = soup.find_all('a', class_='csprite_dltorrent')
                    obj['torrent'] = a_tag[0]['href']
                    obj['magnet'] = a_tag[-1]['href']
                    obj['hash'] = re.search(
                        r'([{a-f\d,A-F\d}]{32,40})\b', obj['magnet']).group(0)
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

    def _parser(self, htmls, idx=0):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')
                list_of_urls = []
                my_dict = {
                    'data': []
                }

                for tr in soup.find_all('tr')[idx:]:
                    td = tr.find_all("td")
                    if len(td) == 0:
                        continue
                    name = td[0].get_text(strip=True)
                    url = self.BASE_URL+td[0].find_all('a')[-1]['href']
                    list_of_urls.append(url)
                    added_on_and_category = td[1].get_text(strip=True)
                    date = (added_on_and_category.split('-')[0]).strip()
                    category = (added_on_and_category.split('in')[-1]).strip()
                    size = td[2].text
                    seeders = td[3].text
                    leechers = td[4].text
                    my_dict['data'].append({
                        'name': name,
                        'size': size,
                        'date': date,
                        'category': category if category != date else None,
                        'seeders': seeders,
                        'leechers': leechers,
                        'url': url,
                    })
                    if len(my_dict['data']) == self.LIMIT:
                        break
                try:
                    div = soup.find('div', class_='search_stat')
                    current_page = int(div.find('span', class_='active').text)
                    total_page = int((div.find_all('a'))[-2].text)
                    if current_page > total_page:
                        total_page = current_page
                    my_dict['current_page'] = current_page
                    my_dict['total_pages'] = total_page
                except:
                    pass
                return my_dict, list_of_urls
        except:
            return None, None

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + \
                "/search/all/{}//{}".format(query, page)
            return await self.parser_result(start_time, url, session, idx=5)

    async def parser_result(self, start_time, url, session, idx=0):
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
            url = self.BASE_URL + '/top100'
            return await self.parser_result(start_time, url, session)

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            if not category:
                url = self.BASE_URL + '/latest100'
            else:
                category = (category).capitalize()
                if category == 'Apps':
                    category = 'Applications'
                elif category == 'Tv':
                    category = 'TV-shows'
                url = self.BASE_URL + \
                    "/browse-torrents/{}/date/{}/".format(category, page)
            return await self.parser_result(start_time, url, session)
