# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render

from .models import *

def index(request):
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

    funds_list = InvestmentFund.objects.all()
    funds_list = sorted(funds_list, cmp=cmpfun)

    import collections
    data = collections.defaultdict(dict)
    for dp in DataPoint.objects.all():
        data[dp.price_date][dp.fund.name] = dp.value

    paid_data = PolicyOperation.objects.filter(operation_type=u'Wp\u0142aty').order_by('operation_date')
    paid_data_dates = [op.operation_date for op in paid_data]
    paid_data_amounts = [op.operation_amount for op in paid_data]
    paid_data_sums = [sum(paid_data_amounts[0:i+1]) for i in range(len(paid_data))]
    paid_data = zip(paid_data_dates, paid_data_sums)
    for date, sum_payments in paid_data:
        data[date]['sum_payments'] = sum_payments
    last_day = sorted(data.keys())[-1]
    data[last_day]['sum_payments'] = paid_data_sums[-1]

    data = sorted(data.items())

    context = {'funds_list': funds_list,
               'data': data
               }
    return render(request, 'report/index.html', context)


def fund_details(request, fund_id):
    fundobj = get_object_or_404(InvestmentFund, pk=fund_id)
    data_list = DataPoint.objects.filter(fund=fundobj).order_by('-price_date')
    context = {'fund_name': fundobj.name,
               'data_list': data_list}
    return render(request, 'report/fund_details.html', context)
