from django.db.utils import OperationalError

from bank_parser.models import RatesHistory, Bank, Currency
from celery import shared_task
from bank_parser.parser import Parser
from bank_parser.utils import today_db, check_banks, create_currencies, make_empty_rate

from curs_bancar.elastic import es


@shared_task(name='parse_data')
def parse_data(short_name, date=today_db()):
    """parse rates from web"""
    try:
        executor = Parser.executor[short_name.lower()]()
        executor.db_date = date
        rates = executor.parse()
        for rate in rates:
            RatesHistory.objects.get_or_create(
                currency=Currency.objects.get(abbr=rate['abbr']),
                bank=Bank.objects.get(short_name__iexact=rate['short_name']),
                rate_sell=rate['rate_sell'],
                rate_buy=rate['rate_buy'],
                date=date
            )

    # if not found data, make empty rate
    except IndexError as exc:
        make_empty_rate(short_name, date)


@shared_task(name='parse_all_beat')
def parse_all_beat():
    """Scheduled task every day get data from all banks"""
    # Check Bank and Currency tables
    check_banks()
    if not Currency.objects.all().exists():
        create_currencies()

    queryset = Bank.objects.all()
    for bank in queryset:
        if not RatesHistory.objects.filter(bank=bank, date=today_db()).exists():
            parse_data.delay(bank.short_name, today_db())


@shared_task(name='indexation_es_rateshistory')
def indexation_es_rateshistory():
    queryset = RatesHistory.objects.all()
    for index, doc in enumerate(queryset):
        es.add_document(
            index='curs_bancar',
            doc_type='rates-history',
            document=doc.es_doc(),
            document_id=doc.id
        )
