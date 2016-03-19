from django.shortcuts import render

from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the Funds index.")


def fund_details(request, fund_id):
    response = "You're looking at the details of fund %s." % fund_id
    return HttpResponse(response)
