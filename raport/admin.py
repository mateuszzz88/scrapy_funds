from django.contrib import admin

from .models import DataPoint, InvestmentFund

admin.site.register(DataPoint)
admin.site.register(InvestmentFund)