from django.db.utils import OperationalError

from bank_parser.models import RatesHistory, Bank, Currency
from curs_bancar.celery import app
from bank_parser.parser import Parser
from bank_parser.utils import today_db, check_banks, create_currencies, make_empty_rate

from curs_bancar.elastic import es


@app.task(bind=True, default_retry_delay=3)
def parse_data(self, short_name, date=today_db()):
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

    except OperationalError as exc:
        raise self.retry(exc=exc)

    # if not found data, make empty rate
    except IndexError as exc:
        make_empty_rate(short_name, date)


@app.task(bind=True)
def parse_all_beat(self):
    """Scheduled task every day get data from all banks"""
    # Check Bank and Currency tables
    check_banks()
    if not Currency.objects.all().exists():
        create_currencies()

    queryset = Bank.objects.all()
    for bank in queryset:
        if not RatesHistory.objects.filter(bank=bank, date=today_db()).exists():
            parse_data.apply_async((bank.short_name, today_db()))


@app.task(bind=True)
def indexation_es_rateshistory(self):
    queryset = RatesHistory.objects.all()
    for index, doc in enumerate(queryset):
        es.add_document(
            index='curs_bancar',
            doc_type='rates-history',
            document=doc.es_doc(),
            document_id=doc.id
        )
