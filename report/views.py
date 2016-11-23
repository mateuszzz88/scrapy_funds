# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render
from pprint import pprint as pp
from collections import defaultdict

from .models import *

SUM_PAYMENTS = 'sum_payments'


def policy_details(request, policy_id):
    def cmpfun(a, b):
        afirst, alast = a.edge_datapoints()
        bfirst, blast = b.edge_datapoints()
        afirst, alast, bfirst, blast = afirst.price_date, alast.price_date, bfirst.price_date, blast.price_date

        if alast == blast:
            if afirst == bfirst:
                return 0
            elif afirst < bfirst: return -1
            else: return 1
        else:
            if alast == blast: return 0
            elif alast < blast: return 1
            else: return -1

    policy = get_object_or_404(Policy, pk=policy_id)
    funds_list = policy.investmentfund_set.exclude(name='(none)')
    funds_list = sorted(funds_list, cmp=cmpfun)
    # funds_list = sorted(funds_list, key=operator.attrgetter('name'))

    import collections
    data = collections.defaultdict(dict)
    for dp in DataPoint.objects.filter(fund__in=funds_list):
        data[dp.price_date][dp.fund.name] = dp.value
    OP_TYPES = [PolicyOperation.DEPOSIT, PolicyOperation.WITHDRAW]
    paid_data = policy.policyoperation_set.filter(operation_type__in=OP_TYPES).order_by('operation_date')
    paid_data_dates = [op.operation_date for op in paid_data]
    paid_data_amounts = [op.operation_amount for op in paid_data]
    paid_data_sums = [sum(paid_data_amounts[0:i+1]) for i in range(len(paid_data))]
    paid_data = zip(paid_data_dates, paid_data_sums)
    for date, sum_payments in paid_data:
        data[date][SUM_PAYMENTS] = sum_payments
    last_day = sorted(data.keys())[-1]
    if paid_data:
        data[last_day][SUM_PAYMENTS] = paid_data_sums[-1]

    data = sorted(data.items())

    # add guards with 0 value and fill gaps in sum_payments values
    if SUM_PAYMENTS not in data[0][1].keys():
        data[0][1][SUM_PAYMENTS] = 0
    for idx, (day, values_dict) in enumerate(data):
        for fund, val in values_dict.items():
            if val == 0: continue
            if fund == SUM_PAYMENTS: continue
            if idx != 0 and fund not in data[idx-1][1].keys():
                data[idx-1][1][fund] = 0
            if idx != len(data)-1 and fund not in data[idx+1][1].keys():
                data[idx+1][1][fund] = 0
        if idx>0 and SUM_PAYMENTS not in values_dict.keys():
            data[idx][1][SUM_PAYMENTS] = data[idx - 1][1][SUM_PAYMENTS]

    context = {'funds_list': funds_list,
               'data': data
               }
    return render(request, 'report/policy_details.html', context)


def fund_details(request,  fund_id):
    fund = get_object_or_404(InvestmentFund, pk=fund_id)
    data_list = DataPoint.objects.filter(fund=fund).order_by('-price_date')
    operations = [(od.operation.operation_date, od.money_transfer, od.operation.operation_type)
                  for od in fund.policyoperationdetail_set.order_by('operation__operation_date')]
    operations_dict = defaultdict(lambda : defaultdict(float))
    for op_date, op_transfer, op_type in operations:
        operations_dict[op_date][op_type] += op_transfer
    # TODO change to normal dicts
    # import pdb; pdb.set_trace()
    context = {'fund_name': fund.name,
               'data_list': data_list,
               'operations': operations_dict}
    return render(request, 'report/fund_details.html', context)


def policy_list(request):
    policies = [(policy, 0, 0) for policy in Policy.objects.all()]
    # import pdb; pdb.set_trace()
    context = {'policies': policies}
    return render(request, 'report/policy_list.html', context)