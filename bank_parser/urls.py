from django.urls import path

from .views import ParseBankView, BankListView, BestPriceView, ElasticParseView, FastSeacrhView

urlpatterns = [
    path('', BankListView.as_view(), name='bank_list_url'),
    path('get/<str:short_name>/', ParseBankView.as_view(), name='item_bank_url'),
    path('best/<str:abbr>/', BestPriceView.as_view(), name='best_price_url'),

    path('get_elastic/', ElasticParseView.as_view(), name='elastic_parse_url'),
    path('fast_search/<str:abbr>/', FastSeacrhView.as_view(), name='fast_search_url'),
]
