from django.db.utils import OperationalError

from bank_parser.models import RatesHistory, Bank, Currency
from curs_bancar.celery import app
from bank_parser.parser import Parser
from bank_parser.utils import today_db, last_day


@app.task(bind=True, default_retry_delay=15)
def save_data(self, date, rates):
    """save parsed rates to db"""
    for rate in rates:
        try:
            RatesHistory.objects.create(
                currency=Currency.objects.get(abbr=rate['abbr']),
                bank=Bank.objects.get(short_name__iexact=rate['short_name']),
                rate_sell=rate['rate_sell'],
                rate_buy=rate['rate_buy'],
                date=date
            )
        except OperationalError as exc:
            raise self.retry(exc=exc)


@app.task(bind=True, default_retry_delay=15)
def parse_bank(self, short_name, date=today_db()):
    """parse rates from web"""
    try:
        executor = Parser.executor[short_name.lower()]()
        executor.db_date = date
        return executor.parse()
    except OperationalError as exc:
        raise self.retry(exc=exc)

    # if not found data, use data for last day
    except IndexError as exc:
        self.retry(args=(short_name, last_day(date)), exc=exc, countdown=1)

