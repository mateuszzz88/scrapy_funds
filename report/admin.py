from django.contrib import admin

from .models import *

admin.site.register(DataPoint)
admin.site.register(InvestmentFund)
admin.site.register(PolicyOperation)
admin.site.register(Policy)
admin.site.register(PolicyOperationDetail)