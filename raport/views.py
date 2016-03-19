from django.shortcuts import get_object_or_404, render

from django.http import HttpResponse
from .models import InvestmentFund, DataPoint


def index(request):
    funds_list = InvestmentFund.objects.order_by('name')
    context = {'funds_list': funds_list}
    return render(request, 'raport/index.html', context)


def fund_details(request, fund_id):
    # question = get_object_or_404(Question, pk=question_id)
    # return render(request, 'polls/detail.html', {'question': question})

    response = "You're looking at the details of fund %s." % fund_id
    return HttpResponse(response)
