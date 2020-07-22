from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from bank_parser.models import Bank, RatesHistory
from bank_parser.serializers import CurrentRatesSerializer
from bank_parser.utils import (today_db)


class ParseBankView(GenericAPIView):
    """Get rates for selected bank and date"""
    permission_classes = (AllowAny,)
    authentication_classes = (JWTAuthentication,)

    queryset = Bank.objects.filter().exclude(short_name='BNM')

    def get(self, request):
        date = (request.GET.get('date') or today_db())
        rates = RatesHistory.objects.filter(date=date, bank__in=self.queryset).exclude(currency__abbr='empty')

        serializer = CurrentRatesSerializer(rates, many=True)
        return Response(serializer.data)
