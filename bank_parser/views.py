from django.core.exceptions import ObjectDoesNotExist
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404

import datetime
import requests
from bs4 import BeautifulSoup

from .serializers import BankSerializer, CurrentRatesSerializer, RatesHistorySerializer
from .parser import BNMParser, Parser
from .models import Bank, Currency, RatesHistory

today = datetime.date.today().strftime("%d.%m.%Y")
date_raw = today.split('.')
valid_date = date_raw[2] + "-" + date_raw[1] + "-" + date_raw[0]


class ParseBankView(GenericAPIView):
    serializer_class = BankSerializer
    permission_classes = [AllowAny, ]
    authentication_classes = ()

    queryset = Bank.objects.all()

    def get(self, request, short_name):
        if not self.queryset.all().exists():
            self.create_banks()
        # fill currecies table if empty
        if not Currency.objects.all().exists():
            self.create_currencies()

        if short_name == 'all':
            for bank in self.queryset.all():
                try:
                    self.parse_bank(bank)
                except AttributeError:
                    pass
            rates = RatesHistory.objects.filter(date=valid_date)

        else:
            bank = get_object_or_404(Bank, short_name__iexact=short_name)
            try:
                self.parse_bank(bank)
            except AttributeError:
                return Response({'error': 'Not exists data try later'})
            rates = RatesHistory.objects.filter(date=valid_date, bank=bank)
        serializer = CurrentRatesSerializer(rates, many=True)

        return Response(serializer.data)

    @staticmethod
    def parse_bank(bank):
        executor = Parser.executor[bank.short_name.lower()]()

        if not RatesHistory.objects.filter(date=valid_date, bank=executor.bank).exists():
            try:
                executor.parse()
                for rate in executor.rates:
                    new_rate = RatesHistory(
                        currency=Currency.objects.get(abbr=rate['abbr']),
                        bank=bank,
                        rate_sell=rate['rate_sell'],
                        rate_buy=rate['rate_buy']
                    )
                    new_rate.save()
            except ValueError:
                return Response({'error': 'Not exists data try later'})

    @staticmethod
    def create_banks():
        banks_list = [
            {
                'name': 'Banca Națională a Moldovei',
                'short_name': 'BNM',
                'url': 'https://www.bnm.md/en/official_exchange_rates?get_xml=1&date='
            },
            {
                'name': 'Moldova Agroindbank',
                'short_name': 'MAIB',
                'url': 'https://www.maib.md/en/start/'
            },
            {
                'name': 'Moldindconbank',
                'short_name': 'MICB',
                'url': 'https://www.micb.md/'
            },
            {
                'name': 'Victoria Bank',
                'short_name': 'Victoria',
                'url': 'https://www.victoriabank.md/ro/currency-history'
            },
            {
                'name': 'Mobias Banca',
                'short_name': 'Mobias',
                'url': 'https://mobiasbanca.md/exrates'
            },
        ]
        for bank in banks_list:
            Bank.objects.create(
                name=bank['name'],
                short_name=bank['short_name'],
                url=bank['url']
            )

    @staticmethod
    def create_currencies():
        bnm = Bank.objects.get(short_name__iexact='bnm')
        url = bnm.url + today

        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')
        currency_raw = soup.find_all("valute")

        for currency in currency_raw:
            abbr = currency.find("charcode").string
            name = currency.find("name").string
            Currency.objects.create(
                abbr=abbr,
                name=name
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

    queryset = RatesHistory.objects.filter(date=valid_date)

    def get(self, request, abbr):
        bnm = Bank.objects.get(short_name__iexact='bnm')
        self.queryset = RatesHistory.objects.filter(date=valid_date).exclude(bank=bnm)
        currency = get_object_or_404(Currency, abbr__iexact=abbr)
        rates = self.queryset.filter(currency=currency)

        try:
            best_sell = CurrentRatesSerializer(self.get_best_sell(rates, currency), many=True).data
            best_buy = CurrentRatesSerializer(self.get_best_buy(rates, currency), many=True).data
            answer = {
                'best_sell': best_sell,
                'best_buy': best_buy
            }
            return Response(answer)
        except IndexError:
            return Response({'error': 'not exists data, need to parse'})

    @staticmethod
    def get_best_sell(rates, currency):
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
        best_rates = [rates[0]]
        for rate in rates[1:]:
            if rate.rate_buy < best_rates[0].rate_buy:
                best_rates = list()
                best_rates.append(rate)
            elif rate.rate_buy == best_rates[0].rate_buy:
                best_rates.append(rate)
        return best_rates
