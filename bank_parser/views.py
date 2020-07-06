from django.core.exceptions import ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .serializers import BankSerializer, CurrentRatesSerializer, RatesHistorySerializer
from .tasks import parse_bank, save_data
from .models import Bank, Currency, RatesHistory
from .utils import (today_db,
                    verify_date,
                    check_banks,
                    create_currencies,
                    get_best_buy,
                    get_best_sell,
                    waiting_msg,)


class ParseBankView(GenericAPIView):
    serializer_class = BankSerializer
    # permission_classes = ([IsAuthenticated])
    permission_classes = ([AllowAny])
    authentication_classes = ([JWTAuthentication])

    queryset = Bank.objects.all()

    def get(self, request, short_name):
        date = (request.GET.get('date') or today_db())

        if not verify_date(date):
            return Response({'error': 'can\'t predict', 'date': date})

        # fill banks if not exists
        check_banks()
        # fill currencies table if empty
        if not Currency.objects.all().exists():
            create_currencies()

        try:
            public_only = True
            if not short_name == 'all':
                self.queryset = Bank.objects.filter(short_name__iexact=short_name)
                public_only = False

            have_data = True
            for bank in self.queryset.all():
                if not RatesHistory.objects.filter(date=date, bank=bank).exists():
                    have_data = False
                    try:
                        rates = parse_bank.apply_async((bank.short_name, date), queue='parse_data')
                        save_data.apply_async((rates.get(), date), queue='save_data')

                    except TypeError:
                        continue
                    except AttributeError:
                        return Response({'error': 'Data not found'})

            # Return response without waiting for task finishing
            if not have_data:
                return Response(waiting_msg)

            if public_only:
                rates = RatesHistory.objects.filter(date=date, bank__is_public=public_only, bank__in=self.queryset)
            else:
                rates = RatesHistory.objects.filter(date=date, bank__in=self.queryset)

        except ValidationError:
            return Response({'error': 'Check the date format YYYY-MM-DD'})

        serializer = CurrentRatesSerializer(rates, many=True)

        return Response(serializer.data)


class BankListView(GenericAPIView):
    serializer_class = BankSerializer
    permission_classes = ([IsAuthenticated])
    authentication_classes = ([JWTAuthentication])

    queryset = Bank.objects.all()

    def get(self, request):
        serializer = BankSerializer(self.queryset.all(), many=True)
        return Response(serializer.data)


class BestPriceView(GenericAPIView):
    serializer_class = RatesHistorySerializer
    permission_classes = ([AllowAny])
    # permission_classes = ([IsAuthenticated])
    authentication_classes = ([JWTAuthentication])

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
