from django.contrib import admin

from .models import Bank, Currency, RatesHistory

admin.site.register(Bank)
admin.site.register(Currency)
admin.site.register(RatesHistory)
