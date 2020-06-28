from django.core.exceptions import ObjectDoesNotExist
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404

from .serializers import BankSerializer, CurrentRatesSerializer, RatesHistorySerializer
from .parser import BNMParser, Parser
from .models import Bank, Currency, RatesHistory
from .parser import valid_date


class ParseBankView(GenericAPIView):
    serializer_class = BankSerializer
    permission_classes = [AllowAny, ]
    authentication_classes = ()

    queryset = Bank.objects.all()

    def get(self, request, short_name):
        # fill currecies table if empty
        if not Currency.objects.all().exists():
            currencies = BNMParser()
            currencies.parse()
            for currency in currencies.rates:
                new_currency = Currency()
                try:
                    Currency.objects.get(abbr=currency['abbr'])
                    pass
                except ObjectDoesNotExist:
                    new_currency.abbr = currency['abbr']
                    new_currency.name = currency['name']
                    new_currency.save()

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
        executor = Parser.executor[bank.short_name.lower()]

        executor_obj = executor()

        if not RatesHistory.objects.filter(date=valid_date, bank=executor_obj.bank).exists():
            try:
                executor_obj.parse()
                for rate in executor_obj.rates:
                    new_rate = RatesHistory(
                        currency=Currency.objects.get(abbr=rate['abbr']),
                        bank=bank,
                        rate_sell=rate['rate_sell'],
                        rate_buy=rate['rate_buy']
                    )
                    new_rate.save()
            except ValueError:
                return Response({'error': 'Not exists data try later'})


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

    bnm = Bank.objects.get(short_name__iexact='bnm')
    queryset = RatesHistory.objects.filter(date=valid_date).exclude(bank=bnm)

    def get(self, request, abbr):
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
