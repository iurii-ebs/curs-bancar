from rest_framework import serializers

from bank_parser.models import Bank, Currency, RatesHistory


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['name', 'short_name']


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['name', 'abbr']


class RatesHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RatesHistory
        fields = '__all__'


class CurrentRatesSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer()
    bank = BankSerializer()

    class Meta:
        model = RatesHistory
        fields = ['currency', 'bank', 'rate_sell', 'rate_buy', 'date']


class RatesHistoryItemSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer()
    bank = BankSerializer()

    class Meta:
        model = RatesHistory
        fields = ['currency', 'bank', 'rate_sell', 'rate_buy', 'date']
