from __future__ import unicode_literals

from django.db import models


class Policy(models.Model):
    name = models.CharField(max_length=30)
    company = models.CharField(max_length=20)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=20)

    def __unicode__(self):
        return u"%s (%s@%s)" % (self.name, self.login, self.company)

    def total_deposited(self):
        return int(self.policyoperation_set.filter(operation_type=PolicyOperation.DEPOSIT, operation_amount__lt=30000)\
            .aggregate(models.Sum('operation_amount'))['operation_amount__sum'] or 0)

    def last_value(self):
        funds = [fund for fund in self.investmentfund_set.all()]
        last_days = [fund.edge_datapoints()[1].price_date for fund in funds]
        last_day = max(last_days)
        last_dps = DataPoint.objects.filter(fund__policy=self, price_date=last_day)
        last_vals = [dp.value for dp in last_dps]
        last_val = sum(last_vals)
        # import pdb; pdb.set_trace()
        return last_val

    def clear(self):
        for fund in self.investmentfund_set.all():
            fund.delete()
        for op in self.policyoperation_set.all():
            op.delete()



class InvestmentFund(models.Model):
    name = models.CharField(max_length=200)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('name', 'policy')

    def edge_datapoints(self):
        dps = self.datapoint_set.order_by('price_date')
        return dps[0], dps[dps.count()-1]

    def __unicode__(self):
        if self.datapoint_set.all():
            first, last = self.edge_datapoints()
            return u"%s @ %s (%s -> %s)" % (self.name, self.policy.name, first.price_date, last.price_date)
        else:
            return u"%s @ %s (no data)" % (self.name, self.policy.name, )


class DataPoint(models.Model):
    fund = models.ForeignKey(InvestmentFund, on_delete=models.CASCADE)
    amount = models.FloatField()
    unit_price = models.FloatField()
    price_date = models.DateField()
    value = models.FloatField()
    currency = models.CharField(max_length=20)

    class Meta:
        unique_together = ('fund', 'price_date')

    def __unicode__(self):
        return u"%s @ %s" % (self.fund.name, self.price_date)

    @classmethod
    def latest_date(cls, policy):
        funds = policy.investmentfund_set.all()
        last = sorted([fund.datapoint_set.order_by('-price_date').first().price_date for fund in funds])[-1]
        # last = cls.objects.order_by('-price_date').first()
        return last


class PolicyOperation(models.Model):
    operation_id = models.IntegerField()
    operation_date = models.DateField()
    operation_type = models.CharField(max_length=20)
    operation_amount = models.FloatField(default=0)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('policy', 'operation_id')

    @classmethod
    def latest_date(cls, policy):
        last = policy.policyoperation_set.order_by('-operation_date').first()
        if last:
            return last.operation_date
        return None

    def __unicode__(self):
        return u"%s @ %s(%s)" % (self.operation_type, self.operation_date, self.policy.name)


class PolicyOperationDetail(models.Model):
    operation = models.ForeignKey(PolicyOperation, on_delete=models.CASCADE)
    fund = models.ForeignKey(InvestmentFund)
    money_transfer = models.FloatField()

    class Meta:
        unique_together = ('fund', 'operation')

    def __unicode__(self):
        return self.operation.__unicode__()

PolicyOperation.DEPOSIT = u'Wp\u0142aty'
PolicyOperation.WITHDRAW = u'Wyp\u0142aty'
