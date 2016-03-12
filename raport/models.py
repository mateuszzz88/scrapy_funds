from __future__ import unicode_literals

from django.db import models

class InvestmentFund(models.Model):
    name = models.CharField(max_length=200)


class Datapoint(models.Model):
    fund = models.ForeignKey(InvestmentFund, on_delete=models.CASCADE)
    amount = models.FloatField()
    unitprice = models.FloatField()
    pricedate = models.FloatField()
    value = models.FloatField()
    currency = models.CharField(max_length=20)