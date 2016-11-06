# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from report.models import InvestmentFund, PolicyOperation, PolicyOperationDetail
from items import ScrapyOpenlifeHistoryItem, ScrapyOpenlifeItem, ScrapyOpenlifeHistoryItemDetail
import logging


class DjangoDbPipeline(object):

    def process_item(self, item, spider):
        if type(item) is ScrapyOpenlifeItem:
            self.process_OpenlifeItem(item)
        elif type(item) is ScrapyOpenlifeHistoryItem:
            self.process_HistoryItem(item)
        elif type(item) is ScrapyOpenlifeHistoryItemDetail:
            self.process_HistoryDetail(item)
        else:
            logging.log(logging.ERROR, "handling for unexpected item type %s" % (type(item)))
        return item

    @staticmethod
    def process_OpenlifeItem(item):
        from django.db import IntegrityError
        fund, _ = InvestmentFund.objects.get_or_create(name=item['name'], policy=item['policy'])
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
        if item['amount'] > 29000:  # TODO this is dirty hack to work around parents' multiple policies
            return
        PolicyOperation.objects.update_or_create(operation_id=item['id'],
                                                 operation_amount=item['amount'],
                                                 operation_type=item['type'],
                                                 operation_date=item['date'],
                                                 policy=item['policy'])

    @staticmethod
    def process_HistoryDetail(item):
        policy = item['policy']
        if item['fund_name'] == '(none)':
            fund, _ = InvestmentFund.objects.get_or_create(policy=policy, name=item['fund_name'])
        else:
            fund = policy.investmentfund_set.filter(name__startswith=item['fund_name'])[0]
        operation = PolicyOperation.objects.filter(policy=policy, operation_id=item['op_id'])[0]

        PolicyOperationDetail.objects.update_or_create(operation=operation,
                                                       fund=fund,
                                                       money_transfer=item['money_transfer'])
