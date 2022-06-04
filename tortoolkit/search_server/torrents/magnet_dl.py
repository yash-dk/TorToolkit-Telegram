from bs4 import BeautifulSoup
import time
import asyncio
import aiohttp
import re
import cloudscraper
import requests


class Magnetdl:

    def __init__(self):
        self.BASE_URL = "https://www.magnetdl.com"
        self.LIMIT = None

    def _parser(self, htmls):
        try:
            for html in htmls:
                soup = BeautifulSoup(html, 'lxml')

                my_dict = {
                    'data': []
                }
                table = soup.find('table', class_='download')
                for tr in soup.find_all('tr'):
                    td = tr.find_all("td")
                    if len(td) > 1:
                        name = td[1].find('a').get_text(strip=True)
                        if name != '':
                            magnet = td[0].find('a')['href']
                            try:
                                size = td[5].get_text(strip=True)
                            except IndexError:
                                size = None
                            url = td[1].find('a')['href']
                            date = td[2].get_text(strip=True)
                            seeders = td[6].get_text(strip=True)
                            leechers = td[7].get_text(strip=True)
                            category = td[3].text
                            my_dict['data'].append({
                                'name': name,
                                'size': size,
                                'seeders': seeders,
                                'leechers': leechers,
                                'category': category,
                                'hash': re.search(r'([{a-f\d,A-F\d}]{32,40})\b', magnet).group(0),
                                'magnet': magnet,
                                'url': self.BASE_URL + url,
                                'date': date,

                            })
                        if len(my_dict['data']) == self.LIMIT:
                            break
                total_results = soup.find(
                    'div', id='footer').text.replace(',', '')
                current_page = int(
                    (re.search(r'Page\s\d*', total_results).group(0)).replace("Page ", ''))
                total_pages = int(
                    ((re.search(r'Found\s\d*', total_results).group(0)).replace("Found ", ''))) // 40
                my_dict['current_page'] = current_page
                my_dict['total_pages'] = 30 if total_pages > 30 else total_pages if total_pages != 0 else total_pages+1
                return my_dict
        except:
            return None

    async def _get_html(self, session, url):
        session = cloudscraper.create_scraper(sess=session)
        try:
            return session.get(url).text
        except:
            return None

    async def _get_all_results(self, session, url):
        return await asyncio.gather(asyncio.create_task(self._get_html(session, url)))

    async def search(self, query, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            query = requests.utils.unquote(query)
            query = query.split(' ')
            query = '-'.join(query)
            url = self.BASE_URL + \
                '/{}/{}/se/desc/{}/'.format(query[0], query, page)
            return await self.parser_result(start_time, url, session)

    async def parser_result(self, start_time, url, session):
        data = await self._get_all_results(session, url)
        results = self._parser(data)
        if results != None:
            results['time'] = time.time() - start_time
            results['total'] = len(results['data'])
            return results
        return results

    async def recent(self, category, page, limit):
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            self.LIMIT = limit
            if not category:
                url = self.BASE_URL + '/download/movies/{}'.format(page)
            else:
                if category == 'books':
                    category = "e-books"
                url = self.BASE_URL + \
                    "/download/{}/{}/".format(category, page)
            return await self.parser_result(start_time, url, session)

    #! maximum page in category is 30
