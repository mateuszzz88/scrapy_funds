from django.shortcuts import get_object_or_404, render

from .models import InvestmentFund, DataPoint

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
    context = {'funds_list': funds_list}
    return render(request, 'report/index.html', context)


def fund_details(request, fund_id):
    fundobj = get_object_or_404(InvestmentFund, pk=fund_id)
    data_list = DataPoint.objects.filter(fund=fundobj).order_by('-price_date')
    context = {'fund_name': fundobj.name,
               'data_list': data_list}
    return render(request, 'report/fund_details.html', context)
