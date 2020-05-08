import requests
import bs4
import lxml
import csv
import os
import argparse

from collections import namedtuple

# Аргументы для командной строки
parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', help='Url to parse', type=str)
parser.add_argument('-c', '--count', help='The number of pages to parse', type=int, default=1)
parser.add_argument('-a', '--all', help='Parse all found pages', action='store_true')
parser.add_argument('-n', '--name', help='Set filename', type=str)
args = parser.parse_args()

InnerBlock = namedtuple('Block', 'title,price,date,url')
HEADERS = (
    'Название',
    'Цена',
    'Дата публикации',
    'Ссылка',
)


class Block(InnerBlock):

    def __str__(self):
        return f'{self.title}\t{self.price}\t{self.date}\t{self.url}'


class AvitoParser:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/81.0.4044.122 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ru',
        }
        self.result = []

    def get_page(self, page: int = None):
        params = {
            'radius': 0,
            'user': 1,
        }

        if page and page > 1:
            params['p'] = page

        url = args.url
        r = self.session.get(url, params=params, allow_redirects=True)

        return r.text

    def parse_block(self, item):
        url_block = item.select_one('a.snippet-link')
        href = url_block.get('href')
        url = 'https://www.avito.ru' + href if href else None

        title_block = item.select_one('h3.snippet-title')
        title = title_block.string.strip()

        price_block = item.select_one('span.snippet-price')
        price_block = price_block.get_text('\n')
        price_block = list(filter(None, map(lambda i: i.strip(), price_block.split('\n'))))
        price = price_block[0].replace('\u20bd', '')
        print(price)

        date = None
        date_block = item.select_one('div.snippet-date-info')
        date = date_block.get('data-tooltip').strip()

        return Block(
            url=url,
            title=title,
            price=price,
            date=date,
        )

    def get_pagination_limit(self):
        if args.all:
            text = self.get_page()
            soup = bs4.BeautifulSoup(text, 'lxml')

            container = soup.select('span.pagination-item-1WyVp')
            if container:
                return int(container[-2].get_text())
            else:
                return 1
        else:
            return int(args.count)

    def get_blocks(self, page: int):
        text = self.get_page(page=page)
        soup = bs4.BeautifulSoup(text, 'lxml')

        container = soup.select('div.snippet-horizontal.item.item_table.clearfix.js-catalog-item-enum.item-with'
                                '-contact.js-item-extended')

        for item in container:
            block = self.parse_block(item=item)
            self.result.append(block)

    def save_result(self):
        if args.name:
            filename = str(args.name)
        else:
            filename = 'file.csv'
        path = os.getcwd() + filename
        with open(path, 'w') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(HEADERS)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        pages_count = self.get_pagination_limit()
        for i in range(1, pages_count + 1):
            print(f'Парсинг страницы {i} из {pages_count}')
            self.get_blocks(page=i)
        print('Парсинг завершён! Идёт запись в файл...')
        self.save_result()
        print('Запись в файл завершена')


def main():
    p = AvitoParser()
    p.run()


if __name__ == '__main__':
    main()
