from __future__ import unicode_literals

from django.db import models


class InvestmentFund(models.Model):
    name = models.CharField(max_length=200, unique=True)


class DataPoint(models.Model):
    fund = models.ForeignKey(InvestmentFund, on_delete=models.CASCADE)
    amount = models.FloatField()
    unit_price = models.FloatField()
    price_date = models.DateField()
    value = models.FloatField()
    currency = models.CharField(max_length=20)

    class Meta:
        unique_together = ('fund', 'price_date',)
