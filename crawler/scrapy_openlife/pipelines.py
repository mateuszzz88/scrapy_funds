# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from report.models import InvestmentFund


class DjangoDbPipeline(object):

    def process_item(self, item, spider):
        from django.db import IntegrityError
        fund, _ = InvestmentFund.objects.get_or_create(name=item['name'])
        try:
            dp = fund.datapoint_set.create(amount=item['amount'],
                                           unit_price=item['unitprice'],
                                           price_date=item['pricedate'],
                                           value=item['value'],
                                           currency=item['currency'])
        except IntegrityError:
            pass
        return item
