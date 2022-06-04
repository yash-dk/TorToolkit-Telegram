import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
from ..helper.asyncioPoliciesFix import decorator_asyncio_fix
import re
from ..helper.html_scraper import Scraper


class Yts:

    def __init__(self):
        self.BASE_URL = 'https://yts.mx'
        self.LIMIT = None

    @decorator_asyncio_fix
    async def _individual_scrap(self, session, url, obj):
        try:
            async with session.get(url) as res:
                html = await res.text(encoding="ISO-8859-1")
                soup = BeautifulSoup(html, 'lxml')
                try:
                    name = soup.select_one('div.hidden-xs h1').text
                    div = soup.select('div.hidden-xs h2')
                    date = div[0].text
                    genre = div[1].text.split('/')
                    rating = soup.select_one('[itemprop=ratingValue]').text
                    poster = soup.find(
                        'div', id='movie-poster').find('img')['src'].split('/')
                    poster[-1] = poster[-1].replace('medium', 'large')
                    poster = '/'.join(poster)
                    description = soup.select(
                        'div#synopsis .hidden-xs')[0].text.strip()
                    runtime = soup.select_one(
                        '.tech-spec-info').find_all('div', class_='row')[-1].find_all('div')[-3].text.strip()
                    screenshots = soup.find_all('a', class_='screenshot-group')
                    screenshots = [a['href'] for a in screenshots]
                    torrents = []
                    for div in soup.find_all('div', class_='modal-torrent'):
                        quality = div.find(
                            'div', class_='modal-quality').find('span').text
                        all_p = div.find_all('p', class_='quality-size')
                        quality_type = all_p[0].text
                        size = all_p[1].text
                        torrent_link = div.find(
                            'a', class_='download-torrent')['href']
                        magnet = div.find(
                            'a', class_='magnet-download')['href']
                        hash = re.search(
                            r'([{a-f\d,A-F\d}]{32,40})\b', magnet).group(0)
                        torrents.append({
                            'quality': quality,
                            'type': quality_type,
                            'size':  size,
                            'torrent': torrent_link,
                            'magnet': magnet,
                            'hash': hash
                        })
                    obj['name'] = name
                    obj['date'] = date
                    obj['genre'] = genre
                    obj['rating'] = rating
                    obj['poster'] = poster
                    obj['description'] = description
                    obj['runtime'] = runtime
                    obj['screenshot'] = screenshots
                    obj['torrents'] = torrents
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

    def _parser(self, htmls):
        try:

            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')
                list_of_urls = []
                my_dict = {
                    'data': []
                }
                for div in soup.find_all('div', class_='browse-movie-wrap'):
                    url = div.find('a')['href']
                    list_of_urls.append(url)
                    my_dict['data'].append({
                        'url': url
                    })
                    if len(my_dict['data']) == self.LIMIT:
                        break
                try:
                    ul = soup.find(
                        'ul', class_='tsc_pagination')
                    current_page = ul.find('a', class_='current').text
                    my_dict['current_page'] = int(current_page)
                    if current_page:
                        total_results = soup.select_one(
                            'body > div.main-content > div.browse-content > div > h2 > b').text
                        if ',' in total_results:
                            total_results = total_results.replace(',', '')
                        total_page = int(total_results) / 20
                        my_dict['total_pages'] = int(
                            total_page) + 1 if type(total_page) == float else int(total_page)

                except:
                    pass
                return my_dict, list_of_urls
        except:
            return None, None

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            if page != 1:
                url = self.BASE_URL + \
                    '/browse-movies/{}/all/all/0/latest/0/all?page={}'.format(
                        query, page)
            else:
                url = self.BASE_URL + \
                    '/browse-movies/{}/all/all/0/latest/0/all'.format(query)
            return await self.parser_result(start_time, url, session)

    async def parser_result(self, start_time, url, session):
        htmls = await Scraper().get_all_results(session, url)
        result, urls = self._parser(htmls)
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
            url = self.BASE_URL + "/trending-movies"
            return await self.parser_result(start_time, url, session)

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            url = self.BASE_URL + '/browse-movies/0/all/all/0/featured/0/all'
            return await self.parser_result(start_time, url, session)