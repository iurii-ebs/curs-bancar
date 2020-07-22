import datetime
from time import sleep

import requests
from bs4 import BeautifulSoup
from django.db import OperationalError

from bank_parser.models import Bank, Currency, RatesHistory


def today_bnm():
    # BNM url date format
    return datetime.date.today().strftime("%d.%m.%Y")


def today_db():
    # DB date format
    return datetime.date.today().strftime("%Y-%m-%d")


def verify_date(date):
    # Check if date is valid
    today = datetime.datetime.today()
    value = datetime.datetime.strptime(date, '%Y-%m-%d')
    return False if value > today else True


def check_banks():
    # Check count of banks in DB, if not enough - add
    if Bank.objects.all().count() < len(banks_list):
        # Checks every instance of the bank, if not in the DB, adds
        for bank in banks_list:
            if not Bank.objects.filter(short_name__iexact=bank['short_name']).exists():
                public = True
                if bank['short_name'].lower() == 'bnm':
                    public = False

                Bank.objects.create(
                    name=bank['name'],
                    short_name=bank['short_name'],
                    url=bank['url'],
                    is_public=public
                )


def create_currencies():
    # Fill DB with currencies from BNM
    bnm = Bank.objects.get(short_name__iexact='bnm')
    url = bnm.url + today_bnm()

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    currency_raw = soup.find_all("valute")

    for currency in currency_raw:
        Currency.objects.create(
            abbr=currency.find("charcode").string,
            name=currency.find("name").string
        )
    Currency.objects.create(
        abbr='empty',
        name='no data'
    )


def get_best_sell(rates):
    # get first element as best, and compare with rest rates[1:]
    best_rates = [rates[0]]
    for rate in rates[1:]:
        if rate.rate_sell > best_rates[0].rate_sell:
            best_rates = list()
            best_rates.append(rate)
        elif rate.rate_sell == best_rates[0].rate_sell:
            best_rates.append(rate)
    return best_rates


def get_best_buy(rates):
    # get first element as best, and compare with rest rates[1:]
    best_rates = [rates[0]]
    for rate in rates[1:]:
        if rate.rate_buy < best_rates[0].rate_buy:
            best_rates = list()
            best_rates.append(rate)
        elif rate.rate_buy == best_rates[0].rate_buy:
            best_rates.append(rate)
    return best_rates


def last_day(date):
    new_date = datetime.date.fromisoformat(date) - datetime.timedelta(days=1)
    return new_date.isoformat()


def make_empty_rate(short_name, date=today_db()):
    RatesHistory.objects.get_or_create(
        currency=Currency.objects.get(abbr='empty'),
        bank=Bank.objects.get(short_name__iexact=short_name),
        rate_sell='0',
        rate_buy='0',
        date=date
    )


def have_rates(bank, date=today_db()):
    # Check DB in loop to catch DB lock exception and repeat query
    while True:
        try:
            return RatesHistory.objects.filter(date=date, bank=bank).exists()
        except OperationalError:
            sleep(1)


waiting_msg = {'processing': 'Wait while get data'}

banks_list = [
    {
        'name': 'Banca Națională a Moldovei',
        'short_name': 'BNM',
        'url': 'https://www.bnm.md/en/official_exchange_rates?get_xml=1&date=',
    },
    {
        'name': 'Moldova Agroindbank',
        'short_name': 'MAIB',
        'url': 'https://www.maib.md/en/curs-valutar/fx/'
    },
    {
        'name': 'Moldindconbank',
        'short_name': 'MICB',
        'url': 'https://www.micb.md/bul-new/?'
    },
    # {
    #     'name': 'Victoria Bank',
    #     'short_name': 'Victoria',
    #     'url': 'https://www.victoriabank.md/ro/currency-history'
    # },
    {
        'name': 'Mobias Banca',
        'short_name': 'Mobias',
        'url': 'https://mobiasbanca.md/exrates/'
    },
]
