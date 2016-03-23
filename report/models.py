from __future__ import unicode_literals

from django.db import models


class InvestmentFund(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def edge_datapoints(self):
        dps = self.datapoint_set.order_by('price_date')
        return dps[0], dps[dps.count()-1]

    def __str__(self):
        first, last = self.edge_datapoints()
        return "%s (%s -> %s)" % (self.name, first.price_date, last.price_date)


class DataPoint(models.Model):
    fund = models.ForeignKey(InvestmentFund, on_delete=models.CASCADE)
    amount = models.FloatField()
    unit_price = models.FloatField()
    price_date = models.DateField()
    value = models.FloatField()
    currency = models.CharField(max_length=20)

    class Meta:
        unique_together = ('fund', 'price_date',)

    def __str__(self):
        return "%s @ %s" % (self.fund.name, self.price_date)

    @staticmethod
    def latest_date(cls):
        last = cls.objects.order_by('-price_date').first()
        return last.price_date
