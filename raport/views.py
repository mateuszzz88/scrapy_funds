from django.shortcuts import get_object_or_404, render

from django.http import HttpResponse
from .models import InvestmentFund, DataPoint


def index(request):
    funds_list = InvestmentFund.objects.order_by('name')
    context = {'funds_list': funds_list}
    return render(request, 'raport/index.html', context)


def fund_details(request, fund_id):
    fundobj = get_object_or_404(InvestmentFund, pk=fund_id)
    data_list = DataPoint.objects.filter(fund=fundobj).order_by('-price_date')
    context = {'fund_name': fundobj.name,
               'data_list': data_list}
    return render(request, 'raport/fund_details.html', context)
