from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from bank_parser.serializers import BankSerializer, CurrentRatesSerializer, RatesHistorySerializer
from bank_parser.tasks import indexation_es_rateshistory, parse_data
from bank_parser.models import Bank, Currency, RatesHistory
from bank_parser.utils import (today_db,
                               verify_date,
                               check_banks,
                               create_currencies,
                               get_best_buy,
                               get_best_sell,
                               waiting_msg,
                               have_rates,
                               best_rates, )


class ParseBankView(GenericAPIView):
    """Parse or get rates for selected bank and date"""
    serializer_class = BankSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (JWTAuthentication,)

    queryset = Bank.objects.all()

    def get(self, request, short_name):
        date = (request.GET.get('date') or today_db())

        #
        try:
            if not verify_date(date):
                return Response({'error': 'can\'t predict', 'date': date})
        except ValueError:
            return Response({'error': 'Check the date format YYYY-MM-DD'})

        # fill banks if not exists
        check_banks()
        # fill currencies table if empty
        if not Currency.objects.all().exists():
            create_currencies()

        # try:
        public_only = True
        if not short_name == 'all':
            self.queryset = Bank.objects.filter(short_name__iexact=short_name)
            public_only = False

        wait_flag = False
        for bank in self.queryset.all():

            if not have_rates(bank, date):
                wait_flag = True
                try:
                    parse_data(bank.short_name, date)
                except TypeError:
                    pass
                except AttributeError:
                    return Response({'error': 'Data not found'})

        if wait_flag:
            # Return response without waiting for task finishing
            waiting_msg['date'] = date
            return Response(waiting_msg)

        if public_only:
            rates = RatesHistory.objects.filter(date=date, bank__is_public=public_only, bank__in=self.queryset).exclude(
                currency__abbr='empty')
        else:
            rates = RatesHistory.objects.filter(date=date, bank__in=self.queryset).exclude(
                currency__abbr='empty')

        serializer = CurrentRatesSerializer(rates, many=True)

        return Response(serializer.data)


class BankListView(GenericAPIView):
    """List of all banks"""
    serializer_class = BankSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (JWTAuthentication,)

    queryset = Bank.objects.all()

    def get(self, request):
        serializer = BankSerializer(self.queryset.all(), many=True)
        return Response(serializer.data)


class BestPriceView(GenericAPIView):
    """Filter Rates by by best prices sell/buy"""
    serializer_class = RatesHistorySerializer
    permission_classes = (AllowAny,)
    authentication_classes = (JWTAuthentication,)

    date = ''

    def get(self, request, abbr):
        self.date = (request.GET.get('date') or today_db())
        self.queryset = RatesHistory.objects.filter(date=self.date, bank__is_public=True)

        if not self.queryset.all().exists():
            ParseBankView().get(request, short_name='all')
            self.queryset = RatesHistory.objects.filter(date=self.date, bank__is_public=True)

        currency = get_object_or_404(Currency, abbr__iexact=abbr)
        rates = self.queryset.filter(currency=currency)

        best_sell = CurrentRatesSerializer(get_best_sell(rates), many=True).data
        best_buy = CurrentRatesSerializer(get_best_buy(rates), many=True).data
        answer = {
            'best_sell': best_sell,
            'best_buy': best_buy
        }
        return Response(answer)


class ElasticParseView(GenericAPIView):
    """Fill elastic db with data"""
    serializer_class = BankSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (JWTAuthentication,)

    queryset = ''

    def get(self, request):
        indexation_es_rateshistory()
        return Response(waiting_msg)


class FastSeacrhView(GenericAPIView):
    """
    Try elastic queries here
    Find best rates sell/buy for selected currency
    """
    serializer_class = BankSerializer
    permission_classes = (AllowAny,)
    authentication_classes = (JWTAuthentication,)

    queryset = ''

    def get(self, request, abbr):
        return Response({
            'best_sell': best_rates('rate_sell', abbr),
            'best_buy': best_rates('rate_buy', abbr),
        })
