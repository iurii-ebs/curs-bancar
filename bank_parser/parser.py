from django.shortcuts import get_object_or_404

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests
import datetime

from .models import Bank, Currency

today = datetime.date.today().strftime("%d.%m.%Y")
date_raw = today.split('.')
valid_date = date_raw[2] + "-" + date_raw[1] + "-" + date_raw[0]



bank_list = ['MAIB', 'MICB', 'Victoria', 'Mobias', 'BNM']


class Parser(ABC):
    url = ''
    soup = ''
    executor = {}

    short_name = 'base'

    def __init__(self):
        super().__init__()
        self.bank = get_object_or_404(Bank, short_name__iexact=self.short_name)
        self.url = self.bank.url
        self.rates = list()

    def make_soup(self):
        r = requests.get(self.url)
        self.soup = BeautifulSoup(r.text, 'lxml')

    @abstractmethod
    def parse(self):
        pass

    # decorator for appending classes to dict, without it subclasses can't be used before declaration
    @classmethod
    def add_sub(cls, sub_cls):
        cls.executor[sub_cls.short_name] = sub_cls

    @staticmethod
    def create_rate(abbr, name, rate_sell, rate_buy):
        return {
            "abbr": abbr,
            "name": name,
            "rate_sell": rate_sell,
            "rate_buy": rate_buy,
        }

    def read_standard_table(self, table):
        tbody = table.find('tbody')
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            abbr = tds[0].text.strip()
            rate_sell = float(tds[1].text.strip())
            rate_buy = float(tds[2].text.strip())
            name = Currency.objects.get(abbr=abbr).name

            self.rates.append(self.create_rate(abbr, name, rate_sell, rate_buy))


@Parser.add_sub
class BNMParser(Parser):
    short_name = 'bnm'

    def __init__(self):
        super().__init__()
        self.url += today
        self.make_soup()

    def parse(self):
        currency_raw = self.soup.find_all("valute")

        for currency in currency_raw:
            abbr = currency.find("charcode").string
            name = currency.find("name").string
            rate_sell = float(currency.find("value").string)
            rate_buy = "0"

            self.rates.append(self.create_rate(abbr, name, rate_sell, rate_buy))


@Parser.add_sub
class MAIBParser(Parser):
    short_name = 'maib'

    def __init__(self):
        super().__init__()
        self.make_soup()

    def parse(self):
        table = self.soup.find('table', class_='tb1')

        self.read_standard_table(table)


@Parser.add_sub
class MICBParser(Parser):
    short_name = 'micb'

    def __init__(self):
        super().__init__()
        self.make_soup()

    def parse(self):
        data_raw = self.soup.find('div', id='currancy-rates')
        table = data_raw.find('table')

        self.read_standard_table(table)


@Parser.add_sub
class VictoriaParser(Parser):
    short_name = 'victoria'

    def __init__(self):
        super().__init__()
        self.make_soup()

    def parse(self):
        data_raw = self.soup.find('div', id='currency-tab1')
        table = data_raw.find('table')

        self.read_standard_table(table)


@Parser.add_sub
class MobiasParser(Parser):
    short_name = 'mobias'

    def __init__(self):
        super().__init__()
        self.make_soup()

    def parse(self):
        currencies = ['EUR', 'USD', 'RUB']
        table = self.soup.find('table', id='rates-dynamics')
        tbody = table.find('tbody')
        trs = tbody.find_all('tr')
        for tr in trs:
            if any([currency in tr.text for currency in currencies]):
                tds = tr.find_all('td')
                abbr = tds[1].text.strip()
                rate_sell = float(tds[3].text.strip())
                rate_buy = float(tds[4].text.strip())
                name = Currency.objects.get(abbr=abbr).name

                self.rates.append(self.create_rate(abbr, name, rate_sell, rate_buy))
