from django.db import models


class Bank(models.Model):
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=20)
    url = models.CharField(max_length=150)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.short_name


class Currency(models.Model):
    name = models.CharField(max_length=50)
    abbr = models.CharField(max_length=20)

    def __str__(self):
        return self.abbr


class RatesHistory(models.Model):
    currency = models.ForeignKey(Currency, related_name='rates', on_delete=models.CASCADE)
    bank = models.ForeignKey(Bank, related_name='rates', on_delete=models.CASCADE)
    rate_sell = models.FloatField()
    rate_buy = models.FloatField()
    date = models.DateField(db_index=True, auto_now_add=True)

    def __str__(self):
        return f"{self.bank} \t {self.currency} \t {self.rate_sell} \t {self.rate_buy} \t {self.date}"
