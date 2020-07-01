from django.core.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

import requests
from bs4 import BeautifulSoup

from .serializers import BankSerializer, CurrentRatesSerializer, RatesHistorySerializer
from .parser import Parser, today_bnm, today_db
from .models import Bank, Currency, RatesHistory


class ParseBankView(GenericAPIView):
    serializer_class = BankSerializer
    permission_classes = [AllowAny, ]
    authentication_classes = ()

    queryset = Bank.objects.all()
    date = ''

    def get(self, request, short_name):
        self.date = (request.GET.get('date') or today_db())

        # fill banks if not exists
        if not self.queryset.all().exists():
            self.create_banks()
        # fill currencies table if empty
        if not Currency.objects.all().exists():
            self.create_currencies()

        try:
            if short_name == 'all':
                for bank in self.queryset.all():
                    try:
                        self.parse_bank(bank)
                    except AttributeError:
                        pass
                rates = RatesHistory.objects.filter(date=self.date, bank__is_public=True)

            else:
                bank = get_object_or_404(Bank, short_name__iexact=short_name)
                self.parse_bank(bank)
                rates = RatesHistory.objects.filter(date=self.date, bank__short_name__iexact=short_name)

        except ValidationError:
            return Response({'error': 'Check the date format YYYY-MM-DD'})
        except AttributeError:
            return Response({'error': 'Data not found'})

        serializer = CurrentRatesSerializer(rates, many=True)

        return Response(serializer.data)

    def parse_bank(self, bank, date=''):
        executor = Parser.executor[bank.short_name.lower()]()
        executor.date_string = self.date

        try:
            if not RatesHistory.objects.filter(date=self.date, bank=executor.bank).exists():
                executor.parse()
                for rate in executor.rates:
                    RatesHistory.objects.create(
                        currency=Currency.objects.get(abbr=rate['abbr']),
                        bank=bank,
                        rate_sell=rate['rate_sell'],
                        rate_buy=rate['rate_buy'],
                        date=self.date
                    )
        except:
            raise

    @staticmethod
    def create_banks():
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
            {
                'name': 'Victoria Bank',
                'short_name': 'Victoria',
                'url': 'https://www.victoriabank.md/ro/currency-history'
            },
            {
                'name': 'Mobias Banca',
                'short_name': 'Mobias',
                'url': 'https://mobiasbanca.md/exrates/'
            },
        ]
        for bank in banks_list:
            public = True
            if bank['short_name'].lower() == 'bnm':
                public = False

            Bank.objects.create(
                name=bank['name'],
                short_name=bank['short_name'],
                url=bank['url'],
                is_public=public
            )

    @staticmethod
    def create_currencies():
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


class BankListView(GenericAPIView):
    serializer_class = BankSerializer
    permission_classes = [AllowAny, ]
    authentication_classes = ()

    queryset = Bank.objects.all()

    def get(self, request):
        serializer = BankSerializer(self.queryset.all(), many=True)
        return Response(serializer.data)


class BestPriceView(GenericAPIView):
    serializer_class = RatesHistorySerializer
    permission_classes = [AllowAny, ]
    authentication_classes = ()

    date = ''

    def get(self, request, abbr):
        self.date = (request.GET.get('date') or today_db())
        self.queryset = RatesHistory.objects.filter(date=self.date, bank__is_public=True)

        if not self.queryset.all().exists():
            ParseBankView().get(request, short_name='all')
            self.queryset = RatesHistory.objects.filter(date=self.date, bank__is_public=True)

        currency = get_object_or_404(Currency, abbr__iexact=abbr)
        rates = self.queryset.filter(currency=currency)

        best_sell = CurrentRatesSerializer(self.get_best_sell(rates, currency), many=True).data
        best_buy = CurrentRatesSerializer(self.get_best_buy(rates, currency), many=True).data
        answer = {
            'best_sell': best_sell,
            'best_buy': best_buy
        }
        return Response(answer)

    @staticmethod
    def get_best_sell(rates, currency):
        # get first element as best, and compare with rest rates[1:]
        best_rates = [rates[0]]
        for rate in rates[1:]:
            if rate.rate_sell > best_rates[0].rate_sell:
                best_rates = list()
                best_rates.append(rate)
            elif rate.rate_sell == best_rates[0].rate_sell:
                best_rates.append(rate)
        return best_rates

    @staticmethod
    def get_best_buy(rates, currency):
        # get first element as best, and compare with rest rates[1:]
        best_rates = [rates[0]]
        for rate in rates[1:]:
            if rate.rate_buy < best_rates[0].rate_buy:
                best_rates = list()
                best_rates.append(rate)
            elif rate.rate_buy == best_rates[0].rate_buy:
                best_rates.append(rate)
        return best_rates
