# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from report.models import InvestmentFund, PolicyOperation
from items import ScrapyOpenlifeHistoryItem, ScrapyOpenlifeItem
import logging


class DjangoDbPipeline(object):

    def process_item(self, item, spider):
        if type(item) is ScrapyOpenlifeItem:
            self.process_OpenlifeItem(item)
        elif type(item) is ScrapyOpenlifeHistoryItem:
            self.process_HistoryItem(item)
        else:
            logging.log(logging.ERROR, "handling for unexpected item type %s" % (type(item)))
        return item

    @staticmethod
    def process_OpenlifeItem(item):
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

    @staticmethod
    def process_HistoryItem(item):
        PolicyOperation.objects.update_or_create(operation_id=item['id'],
                                                 operation_amount=item['amount'],
                                                 operation_type=item['type'],
                                                 operation_date=item['date'])
