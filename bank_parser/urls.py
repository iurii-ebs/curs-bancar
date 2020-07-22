from django.urls import path

from bank_parser.views import ParseBankView

urlpatterns = [
    path('get/all/', ParseBankView.as_view(), name='item_bank_url'),
]
