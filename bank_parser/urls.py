from django.urls import path

from .views import ParseBankView, BankListView, BestPriceView

urlpatterns = [
    path('', BankListView.as_view(), name='bank_list_url'),
    path('get/<str:short_name>/', ParseBankView.as_view(), name='test_bank_url'),
    path('best/<str:abbr>/', BestPriceView.as_view(), name='best_price_url')
]
